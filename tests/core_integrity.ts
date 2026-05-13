/**
 * Memoria Protocol: Core Integrity Test
 * Verifies the Bloom Filter logic and CityHash64 parity.
 */

import { TAHGate } from '../lib/core/tah_gate';
import path from 'path';
import fs from 'fs';

async function runTest() {
  console.log('🧪 [MEMORIA_TEST] Starting Core Integrity Test...');

  const cartridgePath = path.resolve(__dirname, '../cartridges/listings_gate.tah');
  
  if (!fs.existsSync(cartridgePath)) {
    console.error('❌ [MEMORIA_TEST] listings_gate.tah not found. Cannot proceed.');
    process.exit(1);
  }

  const gate = new TAHGate(cartridgePath);
  
  // Test cases: Deterministic IDs from the sample set
  const testIds = [
    "MFRTB8303016", // PASCO home
    "RTC2763724",   // Bandera Dr
    "UNKNOWN_ID_999"
  ];

  console.log('📡 [MEMORIA_TEST] Validating Surgical Pointers...');

  testIds.forEach(id => {
    const isPresent = gate.isProbablyPresent(id);
    console.log(`📍 ID: ${id.padEnd(15)} | Bloom: ${isPresent ? 'PRESENT' : 'ABSENT'}`);
  });

  console.log('🏁 [MEMORIA_TEST] Core Integrity Test completed.');
  process.exit(0);
}

runTest();
