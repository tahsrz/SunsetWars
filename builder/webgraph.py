import math
from typing import List, Tuple, Optional

class BitWriter:
    def __init__(self):
        self.buffer = bytearray()
        self.current_byte = 0
        self.bit_count = 0

    def write_bit(self, bit: int):
        self.current_byte = (self.current_byte << 1) | (bit & 1)
        self.bit_count += 1
        if self.bit_count == 8:
            self.buffer.append(self.current_byte)
            self.current_byte = 0
            self.bit_count = 0

    def write_bits(self, value: int, count: int):
        for i in range(count - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def write_unary(self, x: int):
        for _ in range(x):
            self.write_bit(1)
        self.write_bit(0)

    def write_gamma(self, x: int):
        """Elias Gamma encoding for x >= 1."""
        if x < 1: raise ValueError("Gamma encoding requires x >= 1")
        m = int(math.log2(x))
        self.write_unary(m)
        if m > 0:
            self.write_bits(x & ((1 << m) - 1), m)

    def write_zeta(self, x: int, k: int = 3):
        """Zeta encoding (k=3) for x >= 1."""
        if x < 1: raise ValueError("Zeta encoding requires x >= 1")
        h = int(math.log2(x)) // k
        self.write_unary(h)
        left = 1 << (h * k)
        right = 1 << ((h + 1) * k)
        self.write_bits(x - left, (h + 1) * k - 1) # Simplified Zeta for now

    def flush(self):
        if self.bit_count > 0:
            self.current_byte <<= (8 - self.bit_count)
            self.buffer.append(self.current_byte)
            self.current_byte = 0
            self.bit_count = 0
        return bytes(self.buffer)

class BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.bit_pos = 7

    def read_bit(self) -> int:
        if self.pos >= len(self.data): return -1
        bit = (self.data[self.pos] >> self.bit_pos) & 1
        self.bit_pos -= 1
        if self.bit_pos < 0:
            self.bit_pos = 7
            self.pos += 1
        return bit

    def read_bits(self, count: int) -> int:
        val = 0
        for _ in range(count):
            bit = self.read_bit()
            if bit == -1: break
            val = (val << 1) | bit
        return val

    def read_unary(self) -> int:
        count = 0
        while self.read_bit() == 1:
            count += 1
        return count

    def read_gamma(self) -> int:
        m = self.read_unary()
        if m == 0: return 1
        return (1 << m) | self.read_bits(m)

class BVGraphEncoder:
    """
    Lightweight BVGraph (WebGraph) Implementation.
    Focuses on Intervalization and Gap Encoding (Referentiation simplified).
    """
    def __init__(self, window_size: int = 7):
        self.window_size = window_size
        self.history = [] # List of successor lists

    def encode_node(self, node_id: int, successors: List[int]) -> bytes:
        successors = sorted(list(set(successors)))
        writer = BitWriter()
        
        # 1. Outdegree
        writer.write_gamma(len(successors) + 1) # +1 because gamma starts at 1
        
        if not successors:
            return writer.flush()

        # 2. Reference (Disabled for simplicity in v1)
        writer.write_gamma(1) # Distance 0

        # 3. Intervalization
        intervals = []
        residuals = []
        if len(successors) > 0:
            i = 0
            while i < len(successors):
                start = successors[i]
                count = 1
                while i + 1 < len(successors) and successors[i+1] == successors[i] + 1:
                    i += 1
                    count += 1
                
                if count >= 3: # Min interval length
                    intervals.append((start, count))
                else:
                    for j in range(i - count + 1, i + 1):
                        residuals.append(successors[j])
                i += 1

        writer.write_gamma(len(intervals) + 1)
        last_pos = node_id
        for start, length in intervals:
            # Start gap (zigzag)
            gap = start - last_pos
            zigzag = 2 * gap if gap >= 0 else 2 * abs(gap) - 1
            writer.write_gamma(zigzag + 1)
            writer.write_gamma(length - 2) # Length >= 3
            last_pos = start + length

        # 4. Residual Gaps
        # We need to handle residuals relative to the last_pos or node_id
        # Let's use zigzag for the first residual gap too
        for r in residuals:
            gap = r - last_pos
            zigzag = 2 * gap if gap >= 0 else 2 * abs(gap) - 1
            writer.write_gamma(zigzag + 1)
            last_pos = r + 1 # Use r+1 to keep gaps small for sorted residuals

        self.history.append(successors)
        if len(self.history) > self.window_size:
            self.history.pop(0)
            
        return writer.flush()

def test_webgraph():
    encoder = BVGraphEncoder()
    # Test case: node 10 points to [12, 13, 14, 15, 20, 25, 26, 27]
    # Intervals: [12, 4], [25, 3]
    # Residuals: [20]
    links = [12, 13, 14, 15, 20, 25, 26, 27]
    encoded = encoder.encode_node(10, links)
    print(f"Original: {len(links) * 4} bytes (as int32)")
    print(f"Compressed: {len(encoded)} bytes")
    
    # Simple decode verification
    reader = BitReader(encoded)
    outdegree = reader.read_gamma() - 1
    ref_dist = reader.read_gamma() - 1
    num_intervals = reader.read_gamma() - 1
    
    decoded_links = []
    last_pos = 10
    for _ in range(num_intervals):
        zigzag = reader.read_gamma() - 1
        gap = (zigzag // 2) if (zigzag % 2 == 0) else -(zigzag // 2 + 1)
        start = last_pos + gap
        length = reader.read_gamma() + 2
        for i in range(length):
            decoded_links.append(start + i)
        last_pos = start + length
        
    while len(decoded_links) < outdegree:
        zigzag = reader.read_gamma() - 1
        gap = (zigzag // 2) if (zigzag % 2 == 0) else -(zigzag // 2 + 1)
        val = last_pos + gap
        decoded_links.append(val)
        last_pos = val + 1
        
    decoded_links.sort()
    print(f"Decoded: {decoded_links}")
    assert decoded_links == sorted(links)

if __name__ == "__main__":
    test_webgraph()
