using System;
using TAH.Terminal;

class Verify
{
    static void Main()
    {
        string test = "  Texas Real Estate  ";
        ulong m = 10000;
        int k = 3;
        ulong[] indices = CityHash.GetTahIndices(test, m, k);
        Console.WriteLine("Indices for '" + test + "': " + string.Join(", ", indices));
    }
}
