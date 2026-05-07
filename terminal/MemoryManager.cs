using System;
using System.IO;
using System.Collections.Generic;
using System.Text;
using System.Linq;

namespace TAH.Terminal
{
    public class MemoryManager : IDisposable
    {
        private Cartridge _cartridge;
        private string _path;
        
        // TOC maps a CityHash64 of a key to a list of shard indices
        private Dictionary<ulong, List<int>> _toc;

        public MemoryManager(string path)
        {
            _path = path;
            if (!File.Exists(_path))
            {
                throw new FileNotFoundException("Persistent memory cartridge not found.", _path);
            }
            
            _cartridge = new Cartridge(_path);
            _toc = new Dictionary<ulong, List<int>>();
            InitializeTOC();
        }

        private void InitializeTOC()
        {
            Console.WriteLine(string.Format("[MemoryManager] Indexing {0} shards...", _cartridge.ShardCount));
            // In a production TAH file, the TOC might be pre-baked into the binary.
            // For this implementation, we build it JIT from the shard content 
            // to fulfill the "CityHash Indexing" requirement.
            
            for (int i = 0; i < _cartridge.ShardCount; i++)
            {
                string content = _cartridge.GetShardText(i);
                string[] words = content.ToLower().Trim().Split(new[] { ' ', '\n', '\r', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                
                // Index individual words (Unigrams)
                foreach (var word in words.Distinct())
                {
                    byte[] bytes = Encoding.UTF8.GetBytes(word);
                    ulong hash = CityHash.CityHash64(bytes);
                    
                    if (!_toc.ContainsKey(hash)) _toc[hash] = new List<int>();
                    _toc[hash].Add(i);
                }
            }
            Console.WriteLine(string.Format("[MemoryManager] TOC initialized with {0} unique keys.", _toc.Count));
        }

        public string PullMemory(string input)
        {
            string cleanInput = input.ToLower().Trim();
            
            // 1. Probabilistic Gate: Bloom Filter Check
            // This avoids even looking at the TOC or the disk if it's definitely not there.
            if (!_cartridge.ContainsKeyword(cleanInput))
            {
                return null;
            }

            // 2. Deterministic Lookup: CityHash TOC
            byte[] inputBytes = Encoding.UTF8.GetBytes(cleanInput);
            ulong inputHash = CityHash.CityHash64(inputBytes);

            List<int> indices;
            if (_toc.TryGetValue(inputHash, out indices))
            {
                // Return the first matching shard for now (simplest "pull")
                // In a more complex version, we'd rank them.
                return _cartridge.GetShardText(indices[0]);
            }

            return null;
        }

        public void Dispose()
        {
            if (_cartridge != null)
            {
                _cartridge.Dispose();
            }
        }
    }
}
