import sys
import os
from swarm_builder import SwarmMemoriaBuilder

def build_security_architect():
    builder = SwarmMemoriaBuilder()
    
    # --- CLOUD SECURITY SECTOR ---
    
    # 1. Zero Trust Architecture (NIST SP 800-207)
    zt_text = (
        "Zero Trust Architecture (NIST SP 800-207): Identity is the new perimeter. "
        "Principles: Explicit Verification (always authenticate/authorize), Least Privilege (PoLP via JIT/JEA), "
        "and Assume Breach (segmentation and monitoring). Access is granted per-session based on user/device/risk signals."
    )
    zt_off = builder.add_swarm_shard(zt_text)
    builder.register_symbol("ZERO_TRUST_NIST", zt_off)
    
    # 2. IAM Hardening (AWS & Azure)
    iam_text = (
        "IAM Hardening: AWS SCPs (Service Control Policies) and Azure PIM (Privileged Identity Management) "
        "are critical for restricting high-risk actions. Use Managed Identities/IAM Roles to eliminate static credentials. "
        "MFA is mandatory for all console/CLI access. Root/Global Admin accounts must be break-glass only."
    )
    iam_off = builder.add_swarm_shard(iam_text, symbols=["ZERO_TRUST_NIST"])
    builder.register_symbol("IAM_HARDENING", iam_off)
    
    # 3. MITRE ATT&CK for Cloud
    mitre_text = (
        "MITRE ATT&CK for Cloud Mitigations: T1078 (Valid Accounts) -> MFA + Conditional Access. "
        "T1098 (Account Manipulation) -> Monitoring CreateUser/AddMemberToRole events. "
        "T1548 (Abuse Elevation) -> Permission Boundaries and Custom RBAC. "
        "T1550 (Use Alternate Auth) -> Transition to Managed Identities to prevent token theft."
    )
    mitre_off = builder.add_swarm_shard(mitre_text, symbols=["IAM_HARDENING"])
    builder.register_symbol("MITRE_CLOUD_OPS", mitre_off)

    # --- CRYPTOGRAPHY SECTOR ---

    # 4. Asymmetric Primitives (ECC)
    ecc_text = (
        "ECC (Elliptic Curve Cryptography): 256-bit ECC matches 3072-bit RSA security with lower CPU/bandwidth. "
        "Core Primitives: ECDSA for signatures (ES256 in JWTs), ECDHE for key exchange with Perfect Forward Secrecy (PFS), "
        "and Ed25519 for high-speed, side-channel resistant signatures."
    )
    ecc_off = builder.add_swarm_shard(ecc_text)
    builder.register_symbol("ECC_PRIMITIVES", ecc_off)

    # 5. Zero-Knowledge Proofs (ZKP)
    zkp_text = (
        "Zero-Knowledge Proofs: Proving statements without revealing underlying data. "
        "zk-SNARKs: Succinct, fast verification, requires trusted setup. "
        "zk-STARKs: Scalable, transparent, quantum-resistant, no trusted setup. "
        "Patterns: Selective Disclosure (age verification) and Confidential Transactions."
    )
    zkp_off = builder.add_swarm_shard(zkp_text, symbols=["ECC_PRIMITIVES"])
    builder.register_symbol("ZK_PROOFS", zkp_off)

    # 6. HSM & Secure Enclaves
    hardware_text = (
        "Hardware Root of Trust: HSMs protect keys (Vault pattern); Secure Enclaves (TEE) protect data-in-use (Fortress pattern). "
        "AWS Nitro Enclaves allow processing sensitive data (like NTREIS/MLS) in isolated memory. "
        "Defense-in-depth: HSM stores Root Keys, Enclave uses wrapped session keys for high-frequency processing."
    )
    hardware_off = builder.add_swarm_shard(hardware_text, symbols=["ZERO_TRUST_NIST", "ECC_PRIMITIVES"])
    builder.register_symbol("HARDWARE_SECURITY", hardware_off)

    # Save the cartridge
    builder.save_prototype("cartridges/security_architect")
    print("Security Architect Cartridge Compiled (v3.5 Swarm Protocol).")

if __name__ == "__main__":
    # Ensure builder is in path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    build_security_architect()
