# Contributing to Anaya AI

Thanks for helping. Anaya is a small project, so the process is light.

## Set up

```powershell
git clone https://github.com/nextginfosoft/Anaya-AI.git
cd Anaya-AI
.\scripts\setup.ps1 -SkipModel
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\venv\Scripts\python.exe -m pytest
```

You only need Ollama and a microphone to *run* Anaya; the tests need neither.

## Making a change

1. Open an issue first for anything big, so we agree on the approach.
2. Branch from `main`.
3. Write the change **and a test** for it. Tests use fakes for the microphone, speaker, clipboard, internet and the local model, so they run anywhere.
4. Run `python -m pytest` and make sure everything passes.
5. Open a pull request using the template.

## Conventions

- **Commit messages:** present tense and short ("Add timer parsing", not "Added timer parsing").
- **Code style:** match the surrounding code. `main.py` is one file arranged in labelled sections; add new features in the matching section.
- **Matching commands:** write patterns against the *normalised* text (lower-case, no punctuation, a leading "start"/"launch" becomes "open", and "the/my/a" are dropped). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Privacy rule:** any text that comes from the user's clipboard or selection must be spoken with `speak(..., offline=True)`.
- **Safety rule:** no voice commands that can lose work (shutdown, restart, delete) without a confirmation step.
- **Settings:** read them with `_env("NAME")` so both `ANAYA_NAME` and the legacy `MAYA_NAME` work, and document them in [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- **No secrets** in the repository. `.env` files are ignored.
- Keep `README.md`, `docs/COMMANDS.md` and `CHANGELOG.md` in step with behaviour changes.

## Reporting bugs

Use the bug-report form. Include your Windows version, Python version, the relevant lines from `anaya.log` (remove anything private), and what you said.
For security or privacy problems, see [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Licence

By contributing you agree that your contribution is released under the project's [MIT License](LICENSE).
