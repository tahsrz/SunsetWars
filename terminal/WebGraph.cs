using System;
using System.Collections.Generic;

namespace TAH.Terminal
{
    public class BitReader
    {
        private byte[] _data;
        private int _pos;
        private int _bitPos;

        public BitReader(byte[] data)
        {
            _data = data;
            _pos = 0;
            _bitPos = 7;
        }

        public int ReadBit()
        {
            if (_pos >= _data.Length) return -1;
            int bit = (_data[_pos] >> _bitPos) & 1;
            _bitPos--;
            if (_bitPos < 0)
            {
                _bitPos = 7;
                _pos++;
            }
            return bit;
        }

        public int ReadBits(int count)
        {
            int val = 0;
            for (int i = 0; i < count; i++)
            {
                int bit = ReadBit();
                if (bit == -1) break;
                val = (val << 1) | bit;
            }
            return val;
        }

        public int ReadUnary()
        {
            int count = 0;
            while (ReadBit() == 1)
            {
                count++;
            }
            return count;
        }

        public int ReadGamma()
        {
            int m = ReadUnary();
            if (m == 0) return 1;
            return (1 << m) | ReadBits(m);
        }
    }

    public static class WebGraph
    {
        public static List<int> DecodeLinks(byte[] data, int nodeId, int expectedCount)
        {
            var links = new List<int>();
            if (expectedCount == 0) return links;

            var reader = new BitReader(data);
            
            // 1. Outdegree
            int actualOutdegree = reader.ReadGamma() - 1;
            // 2. Reference (Distance 0 in our v1)
            int refDist = reader.ReadGamma() - 1;
            // 3. Intervals
            int numIntervals = reader.ReadGamma() - 1;

            int lastPos = nodeId;
            for (int i = 0; i < numIntervals; i++)
            {
                int zigzag = reader.ReadGamma() - 1;
                int gap = (zigzag % 2 == 0) ? (zigzag / 2) : -(zigzag / 2 + 1);
                int start = lastPos + gap;
                int length = reader.ReadGamma() + 2;
                for (int j = 0; j < length; j++)
                {
                    links.Add(start + j);
                }
                lastPos = start + length;
            }

            // 4. Residuals
            while (links.Count < actualOutdegree)
            {
                int zigzag = reader.ReadGamma() - 1;
                int gap = (zigzag % 2 == 0) ? (zigzag / 2) : -(zigzag / 2 + 1);
                int val = lastPos + gap;
                links.Add(val);
                lastPos = val + 1;
            }

            links.Sort();
            return links;
        }
    }
}
