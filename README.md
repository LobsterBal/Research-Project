COVERT DECOY-BASED STORAGE: A STEALTHY APPROACH AGAINST COERCION & KEYLOGGERS
======================================================

This project implements a prototype deniable encryption storage system that integrates keystroke dynamics (KD) for behavior-based access control.
The system aims to protect sensitive data even when attackers obtain the password (e.g., via coercion or keylogging) by automatically deciding whether to mount a real volume or a decoy volume based on typing behavior.

**✨ Features**

- Multi-volume deniable encryption: One container holds both a real volume and a decoy volume.

- Behavior-aware access control: Keystroke dynamics (timing features) are used to silently discriminate between legitimate users and impostors.

- AI integration: Random Forest classifier trained on KD data ensures covert authentication.

- User-space prototype: No kernel modifications or special hardware required.

- Decoy redirection: Adversaries who know the correct password but type differently are redirected to a plausible decoy volume.

📂 System Architecture

- User Interface → Enter password.

- Keystroke Capture Module → Record timing features (hold, up–down, down–down, up–up, total time).

- Trained Random Forest Model → Classify user as legitimate or impostor.

- Access Control Logic → Decide to mount real volume, decoy volume, or reject.

- Volume Decryption → Key derived using PBKDF2 → AES-CTR decryption + HMAC integrity.

**⚠️ Disclaimer**

- This is a research project prototype.

- It is intended for academic and experimental purposes only.

- It should not be used as a production security tool, as it may not provide complete protection against all attack vectors.

The author assumes no responsibility for any data loss or misuse resulting from use of this prototype.

🔒 Model Availability

For security reasons, the repository does not include the training dataset or the pre-trained Random Forest model (to avoid leaking password-specific timing features).
If you are interested in experimenting with the model, please contact me directly for controlled access.
