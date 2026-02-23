# Contributing to Uptime Monitor

First off, thank you for considering contributing to this project!

## How Can I Contribute?

### Reporting Bugs
- Use the GitHub Issue Tracker.
- Describe the bug and include steps to reproduce.

### Suggesting Enhancements
- Open an issue and describe the feature.

### Pull Requests
1. Fork the repo.
2. Create a new branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

## Local Development Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/claudiusimion/uptime-monitor.git
   cd uptime-monitor
   ```

2. **Run infrastructure:**
   ```bash
   docker-compose up -d redis postgres kafka
   ```

3. **Install Service Dependencies:**
   Each service has its own `requirements.txt` or `package.json`.

4. **Run services locally (optional):**
   You can run services directly using Python/Node if you prefer not to use Docker for everything during development.

## Style Guides
- Python: Follow **PEP 8**.
- JavaScript: Use **Prettier** for formatting.

## License
By contributing, you agree that your contributions will be licensed under its MIT License.
