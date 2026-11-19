# Security Policy

**Status:** Foundation / no supported production releases. Please do not publicly post credentials, tokens, personally identifying user data or exploit details. For a potential vulnerability, contact the repository maintainer through an appropriate private GitHub security-reporting channel **once explicitly enabled**. Avoid inventing a security mailbox.

Runtime goals: offline without implicit network calls, sandboxed process control for local UCI engines, no shell interpolation of user paths, validated PGN/FEN/CSV import, bounded decompression and file sizes, atomic user-data writes, no execution of unknown model or plugin files by default. Security issues block public distribution until reviewed.
