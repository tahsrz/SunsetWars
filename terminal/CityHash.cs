using System;
using System.Text;

namespace TAH.Terminal
{
    public static class CityHash
    {
        private const ulong K0 = 0xc3a5c85c97cb3127;
        private const ulong K1 = 0xb492b66fbe98f273;
        private const ulong K2 = 0x9ae16a3b2f90404f;
        private const ulong K3 = 0xc949d7c7509e6557;
        private const ulong KMUL = 0x9ddfea08eb382d69;

        private static ulong Rotate(ulong val, int shift)
        {
            return shift == 0 ? val : (val >> shift) | (val << (64 - shift));
        }

        private static ulong ShiftMix(ulong val)
        {
            return val ^ (val >> 47);
        }

        private static ulong HashLen16(ulong u, ulong v)
        {
            ulong a = (u ^ v) * KMUL;
            a ^= a >> 47;
            ulong b = (v ^ a) * KMUL;
            b ^= b >> 47;
            b *= KMUL;
            return b;
        }

        private static ulong WeakHashLen32WithSeeds(ulong w, ulong x, ulong y, ulong z, ulong a, ulong b)
        {
            a += w;
            b = Rotate(b + a + z, 21);
            ulong c = a;
            a += x;
            a += y;
            b += Rotate(a, 44);
            return HashLen16(a + z, b + c); // Note: Original CityHash returns a pair, but we can combine or return as needed.
                                             // In standard CityHash, v and w are pairs of ulongs.
        }
        
        // Proper pair-based WeakHash for parity
        private static (ulong, ulong) WeakHashLen32WithSeedsPair(ulong w, ulong x, ulong y, ulong z, ulong a, ulong b)
        {
            a += w;
            b = Rotate(b + a + z, 21);
            ulong c = a;
            a += x;
            a += y;
            b += Rotate(a, 44);
            return (a + z, b + c);
        }

        private static ulong Fetch64(byte[] data, int offset)
        {
            return BitConverter.ToUInt64(data, offset);
        }

        private static uint Fetch32(byte[] data, int offset)
        {
            return BitConverter.ToUInt32(data, offset);
        }

        private static ulong HashLen0to16(byte[] data, int length)
        {
            if (length > 8)
            {
                ulong a = Fetch64(data, 0);
                ulong b = Fetch64(data, length - 8);
                return HashLen16(a, Rotate(b + (ulong)length, length)) ^ b;
            }
            if (length >= 4)
            {
                ulong a = Fetch32(data, 0);
                return HashLen16((ulong)length + (a << 3), Fetch32(data, length - 4));
            }
            if (length > 0)
            {
                byte a = data[0];
                byte b = data[length >> 1];
                byte c = data[length - 1];
                uint y = (uint)a + ((uint)b << 8);
                uint z = (uint)length + ((uint)c << 2);
                return ShiftMix(y * K2 ^ z * K0) * K2;
            }
            return K0;
        }

        private static ulong HashLen17to32(byte[] data, int length)
        {
            ulong a = Fetch64(data, 0);
            ulong b = Fetch64(data, 8);
            ulong c = Fetch64(data, length - 8);
            ulong d = Fetch64(data, length - 16);
            return HashLen16(Rotate(a - b, 43) + Rotate(c, 30) + d,
                             a + Rotate(b ^ K2, 18) + c);
        }

        public static ulong CityHash64(byte[] data)
        {
            int len = data.Length;
            if (len <= 32)
            {
                if (len <= 16) return HashLen0to16(data, len);
                return HashLen17to32(data, len);
            }
            
            if (len <= 64)
            {
                if (len >= 40)
                {
                    ulong x1 = Fetch64(data, len - 40);
                    ulong y1 = Fetch64(data, len - 16) ^ Fetch64(data, len - 24);
                    ulong z1 = Fetch64(data, len - 8);
                    ulong v0 = Rotate(y1, 33) * K1;
                    ulong v1 = Rotate(y1 + x1, 33) * K1;
                    ulong w0 = Rotate(z1 + v0, 35) * K1 + v1;
                    ulong w1 = Rotate(x1 + y1, 33) * K1;
                    return HashLen16(v0 + v1, w0 + w1);
                }
                else
                {
                    return HashLen17to32(data, len);
                }
            }

            // > 64 logic
            ulong x = Fetch64(data, 0);
            ulong y = Fetch64(data, len - 16) ^ Fetch64(data, len - 32);
            ulong z = Fetch64(data, len - 8);
            ulong v0_2 = Rotate(y, 33) * K1;
            ulong v1_2 = Rotate(y + x, 33) * K1;
            ulong w0_2 = Rotate(z + v0_2, 35) * K1 + v1_2;
            ulong w1_2 = Rotate(x + y, 33) * K1;
            x = Rotate(x + y, 42) * K1;

            int offset = 0;
            while (len - offset > 64)
            {
                x = Rotate(x + y + v0_2 + Fetch64(data, offset + 8), 37) * K1;
                y = Rotate(y + v1_2 + Fetch64(data, offset + 48), 42) * K1;
                x ^= w1_2;
                y += v0_2 + Fetch64(data, offset + 40);
                z = Rotate(z + w0_2, 33) * K1;
                
                var v = WeakHashLen32WithSeedsPair(Fetch64(data, offset), Fetch64(data, offset + 16), Fetch64(data, offset + 24), Fetch64(data, offset + 32), v0_2, v1_2);
                v0_2 = v.Item1; v1_2 = v.Item2;
                
                var w = WeakHashLen32WithSeedsPair(Fetch64(data, offset + 32), Fetch64(data, offset + 40), Fetch64(data, offset + 48), Fetch64(data, offset + 56), w0_2, w1_2);
                w0_2 = w.Item1; w1_2 = w.Item2;

                ulong tmp = x; x = z; z = tmp;
                offset += 64;
            }

            return HashLen16(HashLen16(v0_2, v1_2) + ShiftMix(y) * K1 + z,
                             HashLen16(w0_2, w1_2) + x);
        }

        public static ulong CityHash64WithSeed(byte[] data, ulong seed)
        {
            return HashLen16(CityHash64(data) - K2, seed);
        }

        public static ulong[] GetTahIndices(string text, ulong m, int k)
        {
            byte[] x = Encoding.UTF8.GetBytes(text.ToLower().Trim());
            ulong h1 = CityHash64(x);
            
            // h2 using TAH_SALT
            byte[] salt = Encoding.UTF8.GetBytes("TAH_SALT");
            byte[] combined = new byte[x.Length + salt.Length];
            System.Buffer.BlockCopy(x, 0, combined, 0, x.Length);
            System.Buffer.BlockCopy(salt, 0, combined, x.Length, salt.Length);
            ulong h2 = CityHash64(combined);

            ulong[] indices = new ulong[k];
            for (int i = 0; i < k; i++)
            {
                indices[i] = (h1 + (ulong)i * h2) % m;
            }
            return indices;
        }
    }
}
