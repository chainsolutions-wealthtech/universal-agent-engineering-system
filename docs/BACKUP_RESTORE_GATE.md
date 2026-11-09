# Durable-state backup checkpoint

This first SQLite online backup module creates a distinct snapshot, checks database integrity, records SHA-256 and refuses to overwrite existing backups or restored databases. Restore requires the expected SHA-256 and again checks database integrity. CI unit tests use synthetic state only.

**Not a complete disaster-recovery design:** no remote/offsite backups, retention policy, secret encryption, automated scheduler, disaster simulation, point-in-time recovery or verified deployment. Do not use a backup in a shared public artifact or commit any private runtime data.

Next: run backup/restore in an isolated service environment, verify owner access controls and offsite storage, then test recovery under restart and crash scenarios. Main branch protection and independent PR review remain required.
