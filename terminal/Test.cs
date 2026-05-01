using System;
using TAH.Terminal;

class Test {
    static void Main() {
        Console.WriteLine(CityHash.CityHash64(System.Text.Encoding.UTF8.GetBytes("a")));
    }
}
