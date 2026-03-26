# DNSRift

Python CLI tool for Reverse IP lookups & Subdomain enumeration — powered by [dnsrift.net](https://dnsrift.net)

3B+ DNS records. one command. no wordlists needed.

## What it does

- **Reverse IP** — feed it a list of IPs, get back every domain hosted on each one
- **Subdomain Finder** — feed it domains, get all known subdomains
- **Bulk scanning** — loads targets from a `.txt` file and rips through them with 30 threads

No bruteforce. No wordlists. All data pulled straight from DNSRift's 3 billion+ record DNS database.

## Installation

```bash
git clone https://github.com/AoxenSecurity/dnsrift.git
cd dnsrift
python dnsrift.py
```

That's it. Missing packages (`requests`, `colorama`) get installed automatically on first run.

Works on **Python 2.7** and **Python 3.x**.

## Usage

Just run it:

```bash
python dnsrift.py
```

The tool walks you through everything interactively:

1. **API Key** — enter your key or press Enter to use the free plan
2. **Mode** — choose Reverse IP `[1]` or Subdomain `[2]`
3. **Targets** — point it to a `.txt` file with one IP/domain per line

Results get saved automatically to the `results/` folder.

### Example target files

`ips.txt` for Reverse IP mode:
```
8.8.8.8
1.1.1.1
104.21.55.12
```

`domains.txt` for Subdomain mode:
```
example.com
target.org
```

## API Plans

| Plan | Requests | Results/Request | Key Required |
|------|----------|----------------|--------------|
| Free | 100K/day | 100K | No |
| Professional | 1M/month | 500K | Yes |
| Enterprise | 3M/month | Unlimited | Yes |

Free plan works out of the box — no registration, no key.

Paid plans accept USDT (TRC20/Solana) and Bitcoin. Details at [dnsrift.net/pricing](https://dnsrift.net/pricing).

## Links

- Website: [dnsrift.net](https://dnsrift.net)
- API Docs: [dnsrift.net/docs](https://dnsrift.net/docs)

## License

MIT