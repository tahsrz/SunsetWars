using System;
using System.IO;
using System.Collections.Generic;
using System.Text;
using System.Linq;

namespace TAH.Terminal
{
    public struct ShardIndexEntry
    {
        public byte TypeTag;
        public ushort LinkCount;
        public uint LinkOffset;
        public ulong Offset;
        public uint Length;
        public ushort SourceID;
        public ushort RegionID;
        public byte[] Analytics; // 56 bytes
    }

    public struct SearchResult
    {
        public string CartridgeName;
        public int ShardIndex;
        public double Score;
        public string Text;
        public List<int> Links;
    }

    public class Cartridge : IDisposable
    {
        private BinaryReader _reader;
        private FileStream _stream;
        public string Name { get; private set; }
        
        public byte K { get; private set; }
        public ulong M { get; private set; }
        public uint ShardCount { get; private set; }
        public uint AvgComplexity { get; private set; }
        
        public ulong RegistryOffset { get; private set; }
        public uint RegistryLength { get; private set; }
        public ulong LinksOffset { get; private set; }
        public uint LinksLength { get; private set; }

        private byte[] _bloomFilter;
        private ShardIndexEntry[] _shardIndex;
        private byte[] _linksData;

        public Cartridge(string filePath)
        {
            Name = Path.GetFileName(filePath);
            _stream = new FileStream(filePath, FileMode.Open, FileAccess.Read);
            _reader = new BinaryReader(_stream);
            Load();
        }

        private void Load()
        {
            uint magic = _reader.ReadUInt32();
            if (magic != 0x54414821) throw new Exception("Invalid TAH magic number.");

            ushort version = _reader.ReadUInt16();
            K = _reader.ReadByte();
            _reader.ReadByte(); 
            M = _reader.ReadUInt64();
            ShardCount = _reader.ReadUInt32();
            AvgComplexity = _reader.ReadUInt32();

            RegistryOffset = _reader.ReadUInt64();
            RegistryLength = _reader.ReadUInt32();
            LinksOffset = _reader.ReadUInt64();
            LinksLength = _reader.ReadUInt32();

            _stream.Seek(64, SeekOrigin.Begin);

            int bloomByteSize = (int)Math.Ceiling(M / 8.0);
            _bloomFilter = _reader.ReadBytes(bloomByteSize);

            _shardIndex = new ShardIndexEntry[ShardCount];
            for (int i = 0; i < ShardCount; i++)
            {
                _shardIndex[i].TypeTag = _reader.ReadByte();
                _shardIndex[i].LinkCount = _reader.ReadUInt16();
                _shardIndex[i].LinkOffset = _reader.ReadUInt32();
                _stream.Seek(1, SeekOrigin.Current); // Skip 1 padding byte
                
                _shardIndex[i].Offset = _reader.ReadUInt64();
                _shardIndex[i].Length = _reader.ReadUInt32();
                _shardIndex[i].SourceID = _reader.ReadUInt16();
                _shardIndex[i].RegionID = _reader.ReadUInt16();
                _shardIndex[i].Analytics = _reader.ReadBytes(56);
            }

            if (LinksLength > 0)
            {
                _stream.Seek((long)LinksOffset, SeekOrigin.Begin);
                _linksData = _reader.ReadBytes((int)LinksLength);
            }
        }

        public List<int> GetShardLinks(int index)
        {
            if (index < 0 || index >= ShardCount || _shardIndex[index].LinkCount == 0)
                return new List<int>();

            byte[] shardLinksData = new byte[LinksLength - _shardIndex[index].LinkOffset]; // Over-estimate
            Array.Copy(_linksData, (int)_shardIndex[index].LinkOffset, shardLinksData, 0, shardLinksData.Length);
            
            return WebGraph.DecodeLinks(shardLinksData, index, _shardIndex[index].LinkCount);
        }

        public bool ContainsKeyword(string keyword)
        {
            ulong[] indices = CityHash.GetTahIndices(keyword, M, K);
            foreach (var idx in indices)
            {
                int byteIdx = (int)(idx / 8);
                int bitIdx = (int)(idx % 8);
                if ((_bloomFilter[byteIdx] & (1 << bitIdx)) == 0) return false;
            }
            return true;
        }

        public IEnumerable<SearchResult> SearchStream(string query, string[] ngrams)
        {
            for (int i = 0; i < ShardCount; i++)
            {
                double score = CalculateScore(i, query, ngrams);
                if (score > 6.0) // Higher threshold for Pulse
                {
                    yield return new SearchResult {
                        CartridgeName = this.Name,
                        ShardIndex = i,
                        Score = score,
                        Text = GetShardText(i)
                    };
                }
            }
        }

        public double CalculateScore(int index, string query, string[] ngrams)
        {
            var entry = _shardIndex[index];
            switch (entry.TypeTag)
            {
                case 0: return ScoreText(entry, ngrams);
                case 1: return ScoreCoord(entry, query, ngrams);
                case 2: return ScoreImage(entry, ngrams);
                default: return 0;
            }
        }

        private double ScoreText(ShardIndexEntry entry, string[] ngrams)
        {
            double totalScore = 0;
            foreach (var term in ngrams)
            {
                if (!ContainsKeyword(term)) continue;
                ulong[] indices = CityHash.GetTahIndices(term, 448, 4);
                bool match = true;
                foreach (var idx in indices)
                {
                    if ((entry.Analytics[idx / 8] & (1 << (int)(idx % 8))) == 0) { match = false; break; }
                }
                
                if (match)
                {
                    double idf = Math.Log((ShardCount + 0.5) / 1.5 + 1.0);
                    double tf = 1.0;
                    double score = idf * (tf * 2.5) / (tf + 1.5 * (0.25 + 0.75 * (100 / (double)AvgComplexity))); // Defaulting meta to 100
                    if (term.Contains(" ")) score *= 3.0;
                    totalScore += score;
                }
            }
            return totalScore;
        }

        private double ScoreCoord(ShardIndexEntry entry, string query, string[] ngrams)
        {
            if (query.Contains(",")) return 10.0; 
            foreach (var term in ngrams)
            {
                if (!ContainsKeyword(term)) continue;
                ulong[] indices = CityHash.GetTahIndices(term, 384, 4);
                bool match = true;
                foreach (var idx in indices)
                {
                    int byteIdx = (int)(idx / 8) + 8;
                    if ((entry.Analytics[byteIdx] & (1 << (int)(idx % 8))) == 0) { match = false; break; }
                }
                if (match) return 50.0;
            }
            return 0;
        }

        private double ScoreImage(ShardIndexEntry entry, string[] ngrams)
        {
            foreach (var term in ngrams)
            {
                if (!ContainsKeyword(term)) continue;
                ulong[] indices = CityHash.GetTahIndices(term, 384, 4);
                bool match = true;
                foreach (var idx in indices)
                {
                    int byteIdx = (int)(idx / 8) + 8;
                    if ((entry.Analytics[byteIdx] & (1 << (int)(idx % 8))) == 0) { match = false; break; }
                }
                if (match) return 50.0;
            }
            return 0;
        }

        public string GetShardText(int index)
        {
            lock (_stream) 
            {
                _stream.Seek((long)_shardIndex[index].Offset, SeekOrigin.Begin);
                byte[] data = _reader.ReadBytes((int)_shardIndex[index].Length);
                
                // Find null terminator with safety
                int textLen = 0;
                while (textLen < data.Length && data[textLen] != 0) textLen++;
                
                string text = Encoding.UTF8.GetString(data, 0, textLen);
                
                // WebGraph Links (v3.6+)
                var links = GetShardLinks(index);
                if (links.Count > 0)
                {
                    StringBuilder sb = new StringBuilder(text);
                    sb.Append("\n\n[SEE ALSO]");
                    foreach (int linkIdx in links)
                    {
                        sb.Append(string.Format("\n-> Shard {0}", linkIdx));
                        // In a real implementation, we could resolve the title of the linked shard
                    }
                    text = sb.ToString();
                }
                
                return text;
            }
        }

        private string GetPreviewAtOffset(ulong offset)
        {
            // Already inside lock from GetShardText
            long currentPos = _stream.Position;
            try {
                _stream.Seek((long)offset, SeekOrigin.Begin);
                byte[] previewBytes = _reader.ReadBytes(64);
                int len = 0;
                while (len < previewBytes.Length && previewBytes[len] != 0 && previewBytes[len] != 10 && previewBytes[len] != 13) len++;
                if (len == 0) return null;
                return Encoding.UTF8.GetString(previewBytes, 0, len).Trim();
            } catch {
                return null;
            } finally {
                _stream.Seek(currentPos, SeekOrigin.Begin);
            }
        }

        public void Dispose()
        {
            if (_reader != null) _reader.Close();
            if (_stream != null) _stream.Dispose();
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== TAH Terminal v3.1 [Real-Time Pulse] ===");
            
            string cartridgesDir = Directory.Exists("cartridges") ? "cartridges" : Path.Combine("..", "cartridges");
            if (!Directory.Exists(cartridgesDir)) { Console.WriteLine("Error: No cartridges folder."); return; }

            // Initialize MemoryManager
            MemoryManager memoryManager = null;
            string memoryPath = Path.Combine(cartridgesDir, "user_memories.tah");
            if (File.Exists(memoryPath))
            {
                try {
                    memoryManager = new MemoryManager(memoryPath);
                    Console.WriteLine("[MemoryManager] Persistent memory stream active.");
                } catch {}
            }

            // Load pool
            List<Cartridge> pool = new List<Cartridge>();
            foreach (string file in Directory.GetFiles(cartridgesDir, "*.tah"))
            {
                try { pool.Add(new Cartridge(file)); } catch {}
            }
            Console.WriteLine(string.Format("[Pulse] Parallelizing {0} knowledge streams.", pool.Count));
            
            while (true)
            {
                Console.Write("\nPulse Query > ");
                string query = Console.ReadLine();
                if (string.IsNullOrWhiteSpace(query)) break;

                string cleanQuery = query.ToLower().Trim();

                if (memoryManager != null)
                {
                    string memory = memoryManager.PullMemory(cleanQuery);
                    if (memory != null)
                    {
                        Console.WriteLine("\n[DIRECT MEMORY MATCH]");
                        Console.WriteLine(memory);
                        continue;
                    }
                }

                string[] words = cleanQuery.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                List<string> ngrams = new List<string>(words);
                for (int i = 0; i < words.Length - 1; i++) ngrams.Add(words[i] + " " + words[i+1]);
                string[] ngramsArray = ngrams.ToArray();

                Console.WriteLine("[Pulse] Ingesting results...");
                
                List<SearchResult> allResults = new List<SearchResult>();
                object lockObj = new object();

                System.Threading.Tasks.Parallel.ForEach(pool, cartridge => {
                    foreach (var result in cartridge.SearchStream(cleanQuery, ngramsArray))
                    {
                        lock (lockObj)
                        {
                            allResults.Add(result);
                            // Compact pulse feedback
                            Console.WriteLine(string.Format("+ {0} [Score: {1:F1}]", result.CartridgeName, result.Score));
                        }
                    }
                });

                allResults.Sort((x, y) => y.Score.CompareTo(x.Score));

                if (allResults.Count == 0)
                {
                    Console.WriteLine("No matches found.");
                }
                else
                {
                    Console.WriteLine("\n--- TOP KNOWLEDGE ---");
                    // Take only unique best results to avoid redundancy between test cartridges
                    var uniqueResults = new HashSet<string>();
                    int shown = 0;
                    for (int i = 0; i < allResults.Count && shown < 3; i++)
                    {
                        var res = allResults[i];
                        string snippet = res.Text.Substring(0, Math.Min(50, res.Text.Length));
                        if (uniqueResults.Add(snippet))
                        {
                            Console.WriteLine(string.Format("\n[RANK {0} | SOURCE: {1}]", shown+1, res.CartridgeName));
                            Console.WriteLine(res.Text);
                            shown++;
                        }
                    }
                }
            }

            foreach (var c in pool) c.Dispose();
            if (memoryManager != null) memoryManager.Dispose();
        }
    }
}
