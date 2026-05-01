using System;
using System.IO;
using System.Collections.Generic;
using System.Text;

namespace TAH.Terminal
{
    public struct ShardIndexEntry
    {
        public ulong Offset;
        public uint Length;
        public uint WordCount;
        public byte[] LocalBloom;
    }

    public class Cartridge : IDisposable
    {
        private BinaryReader _reader;
        private FileStream _stream;
        
        public byte K { get; private set; }
        public ulong M { get; private set; }
        public uint ShardCount { get; private set; }
        public uint AvgShardLen { get; private set; }
        private byte[] _bloomFilter;
        private ShardIndexEntry[] _shardIndex;

        public Cartridge(string filePath)
        {
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
            AvgShardLen = _reader.ReadUInt32();

            _stream.Seek(64, SeekOrigin.Begin);

            int bloomByteSize = (int)Math.Ceiling(M / 8.0);
            _bloomFilter = _reader.ReadBytes(bloomByteSize);

            _shardIndex = new ShardIndexEntry[ShardCount];
            for (int i = 0; i < ShardCount; i++)
            {
                _shardIndex[i].Offset = _reader.ReadUInt64();
                _shardIndex[i].Length = _reader.ReadUInt32();
                _shardIndex[i].WordCount = _reader.ReadUInt32();
                _shardIndex[i].LocalBloom = _reader.ReadBytes(64);
            }
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

        public List<int> GetMatchedShardIndices(string keyword)
        {
            var matched = new List<int>();
            ulong[] localIndices = CityHash.GetTahIndices(keyword, 512, 4);

            for (int i = 0; i < ShardCount; i++)
            {
                bool match = true;
                foreach (var idx in localIndices)
                {
                    int byteIdx = (int)(idx / 8);
                    int bitIdx = (int)(idx % 8);
                    if ((_shardIndex[i].LocalBloom[byteIdx] & (1 << bitIdx)) == 0) { match = false; break; }
                }
                if (match) matched.Add(i);
            }
            return matched;
        }

        public string GetShardText(int index)
        {
            _stream.Seek((long)_shardIndex[index].Offset, SeekOrigin.Begin);
            byte[] data = _reader.ReadBytes((int)_shardIndex[index].Length);
            return Encoding.UTF8.GetString(data);
        }

        public uint GetShardWordCount(int index) { return _shardIndex[index].WordCount; }

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
            Console.WriteLine("=== TAH (Terminal AI Hub) v2.0 [BM25 + N-Grams] ===");
            
            string cartridgesDir = Directory.Exists("cartridges") ? "cartridges" : Path.Combine("..", "cartridges");
            if (!Directory.Exists(cartridgesDir)) { Console.WriteLine("Error: No cartridges folder."); return; }

            string[] files = Directory.GetFiles(cartridgesDir, "*.tah");
            for (int i = 0; i < files.Length; i++) Console.WriteLine((i + 1) + ". " + Path.GetFileName(files[i]));

            Console.Write("\nSelect Cartridge > ");
            int index = int.Parse(Console.ReadLine()) - 1;
            
            using (var cartridge = new Cartridge(files[index]))
            {
                Console.WriteLine("Loaded: " + Path.GetFileName(files[index]));
                
                while (true)
                {
                    Console.Write("\nQuery > ");
                    string query = Console.ReadLine();
                    if (string.IsNullOrWhiteSpace(query)) break;

                    string cleanQuery = query.ToLower().Trim();
                    string[] words = cleanQuery.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    
                    List<string> ngrams = new List<string>(words);
                    for (int i = 0; i < words.Length - 1; i++) ngrams.Add(words[i] + " " + words[i+1]);
                    for (int i = 0; i < words.Length - 2; i++) ngrams.Add(words[i] + " " + words[i+1] + " " + words[i+2]);

                    var scores = new double[cartridge.ShardCount];
                    double k1 = 1.5;
                    double b = 0.75;

                    foreach (var term in ngrams)
                    {
                        if (!cartridge.ContainsKeyword(term)) continue;

                        var matchedIndices = cartridge.GetMatchedShardIndices(term);
                        if (matchedIndices.Count == 0) continue;

                        // IDF Calculation
                        double idf = Math.Log((cartridge.ShardCount - matchedIndices.Count + 0.5) / (matchedIndices.Count + 0.5) + 1.0);
                        
                        // Boost for longer N-Grams
                        int termWords = term.Split(' ').Length;
                        if (termWords == 2) idf *= 2.0;
                        if (termWords == 3) idf *= 4.0;

                        foreach (int idx in matchedIndices)
                        {
                            // Simplified TF (since we use Bloom filters, we assume TF=1 or 2 if term is found)
                            double tf = 1.0; 
                            double shardLen = cartridge.GetShardWordCount(idx);
                            double avgLen = cartridge.AvgShardLen;
                            
                            double score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (shardLen / avgLen)));
                            scores[idx] += score;
                        }
                    }

                    var results = new List<KeyValuePair<int, double>>();
                    for (int i = 0; i < scores.Length; i++) if (scores[i] > 0) results.Add(new KeyValuePair<int, double>(i, scores[i]));
                    results.Sort((x, y) => y.Value.CompareTo(x.Value));

                    for (int i = 0; i < Math.Min(3, results.Count); i++)
                    {
                        Console.WriteLine("\n[RANK " + (i+1) + " | SCORE: " + results[i].Value.ToString("F2") + "]");
                        Console.WriteLine(cartridge.GetShardText(results[i].Key));
                    }
                }
            }
        }
    }
}
