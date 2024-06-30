# Changelog

## v0.9.1 (2024-06-30)

### Fix

- Fix licensing classifier (#138) ([`3000743`](https://github.com/chemelli74/aiocomelit/commit/3000743b3779be01ffa121cff043900338a07468))


### Build

- Minor updates (#124) ([`1e8316d`](https://github.com/chemelli74/aiocomelit/commit/1e8316da680062cc23d0dbf82d855af675b5923a))
- Use ruff instead of isort, black, flake8, bandit and some pre-… (#112) ([`8bcf252`](https://github.com/chemelli74/aiocomelit/commit/8bcf25250632e8bfd755460d3840bf731b52774e))


## v0.9.0 (2024-02-23)

### Feature

- Add humidity management (#100) ([`1f7b9a9`](https://github.com/chemelli74/aiocomelit/commit/1f7b9a9e6b0c333bc7311c1e2a8fd40288e28394))


### Build

- Revert config change for actions/checkout@v4 (#101) ([`0235b7c`](https://github.com/chemelli74/aiocomelit/commit/0235b7c935abf32c2dacc7b2265054a5b65d126d))


## v0.8.3 (2024-02-05)

### Fix

- Queue clima calls (#97) ([`90ea471`](https://github.com/chemelli74/aiocomelit/commit/90ea4712beab163ea28de018524972761b176be7))


## v0.8.2 (2024-01-25)

### Fix

- Move math to library (#89) ([`91a1a29`](https://github.com/chemelli74/aiocomelit/commit/91a1a2926eb245323617f3b72c1cd1b1adc44b5d))


## v0.8.1 (2024-01-25)

### Fix

- Move set_clima_status to the correct api (#88) ([`28848c8`](https://github.com/chemelli74/aiocomelit/commit/28848c8944c9031ba84afc83b5510415be8f33ec))


## v0.8.0 (2024-01-25)

### Feature

- Clima set status (#86) ([`58e1691`](https://github.com/chemelli74/aiocomelit/commit/58e1691929e25dad26d267c91ff80e8655f10f39))


### Refactor

- Library_test.py params via json config file (#87) ([`0f46014`](https://github.com/chemelli74/aiocomelit/commit/0f4601449609e9e4b606008c433e40ad81f8b5b1))


## v0.7.5 (2024-01-25)

### Fix

- Improve vedo config retrieval (#85) ([`3cf6a49`](https://github.com/chemelli74/aiocomelit/commit/3cf6a499714c42173c8c985043eb7a68731dd9d9))


## v0.7.4 (2024-01-22)

### Fix

- Check session active on logout and close (#82) ([`0bda7c9`](https://github.com/chemelli74/aiocomelit/commit/0bda7c9980794f5cc77add854f9a1cf50d517b21))


### Build

- Use fork to force python 3.11 (#83) ([`7c4540a`](https://github.com/chemelli74/aiocomelit/commit/7c4540a99484a6f2a237aff1904b9639cba642ed))
- Update semantic-release to 8.x (#81) ([`cdb720f`](https://github.com/chemelli74/aiocomelit/commit/cdb720ff504603b00afe4fca435e6b3ffc8437d9))
- Switch ci to python 3.11 (#80) ([`b5ac23e`](https://github.com/chemelli74/aiocomelit/commit/b5ac23ec862f01f29643c00175878d78b793e99d))


## v0.7.3 (2024-01-10)

### Fix

- Not logged in edge cases (#79) ([`4363dbb`](https://github.com/chemelli74/aiocomelit/commit/4363dbb54d90f5a4fc77a2be17f0df8ef121a09a))


## v0.7.2 (2024-01-10)

### Fix

- Handle notlogged sporadic status (#74) ([`92e5663`](https://github.com/chemelli74/aiocomelit/commit/92e56636d15f95fbbb26011331d53a31938c003d))


## v0.7.1 (2024-01-10)

### Fix

- Improve cookies handling (#72) ([`fdf3bb5`](https://github.com/chemelli74/aiocomelit/commit/fdf3bb52173e6a9888d23b877c925c285676c3bb))


## v0.7.0 (2023-12-16)

### Feature

- Make login a shared method (#64) ([`4862904`](https://github.com/chemelli74/aiocomelit/commit/4862904880eb6d73677f90e7f9a9e74e65d73368))


## v0.6.2 (2023-11-28)

### Fix

- Close session only if available (#60) ([`2acca97`](https://github.com/chemelli74/aiocomelit/commit/2acca97ee3d92ae8bba9c6481ad4461398ccfd21))


## v0.6.1 (2023-11-28)

### Fix

- Recreate closed aiohttp session (#57) ([`98dc8bc`](https://github.com/chemelli74/aiocomelit/commit/98dc8bc3d0bda3c95e4ea2476b32f52e94528473))


## v0.6.0 (2023-11-16)

### Feature

- More alarm data and code cleanup (#52) ([`abddf2a`](https://github.com/chemelli74/aiocomelit/commit/abddf2a3e0ddef609c6461b59d5ee6a49a6d7ecd))


## v0.5.2 (2023-11-13)

### Fix

- Disk i/o pint should run in executor (#53) ([`ad95ade`](https://github.com/chemelli74/aiocomelit/commit/ad95ade1aa6ad94f2433a1c80f828792ce0f6689))


## v0.5.1 (2023-11-13)

### Fix

- Timestamp strftime for windows (#54) ([`1afe620`](https://github.com/chemelli74/aiocomelit/commit/1afe6208e3f0acfd370a8f38c52ae48da5064226))


## v0.5.0 (2023-11-10)

### Feature

- Improve performances (#51) ([`e4f65cb`](https://github.com/chemelli74/aiocomelit/commit/e4f65cba64e570b0e17e4907f7b7c955c4b0195d))


## v0.4.0 (2023-11-09)

### Feature

- Add more logging (#50) ([`70347fe`](https://github.com/chemelli74/aiocomelit/commit/70347fe92c3f315a4935aad71c8111891ac7b80a))


## v0.3.2 (2023-11-09)

### Fix

- Alarm management (#49) ([`64da301`](https://github.com/chemelli74/aiocomelit/commit/64da301ffade967b99f9e8ad750a0363bc23d0a8))


## v0.3.1 (2023-11-05)

### Fix

- Updated headers for new fw versions (#46) ([`1dd99c4`](https://github.com/chemelli74/aiocomelit/commit/1dd99c441f91bf28c83a0fa39ac5f46c38d915ae))


## v0.3.0 (2023-10-17)

### Feature

- Alarm vedo full support (#39) ([`61b6ac2`](https://github.com/chemelli74/aiocomelit/commit/61b6ac2ab38a1ff79a40b7214c2425fd14577380))


## v0.2.0 (2023-10-07)

### Feature

- Add http port parametrization (#34) ([`49540a2`](https://github.com/chemelli74/aiocomelit/commit/49540a298e10b502f159c638918d610a26194348))


## v0.1.2 (2023-10-07)

### Fix

- Variable in _login() (#32) ([`9820838`](https://github.com/chemelli74/aiocomelit/commit/9820838d95cd925c803150f0b3559058a6b8e08c))


## v0.1.1 (2023-10-07)

### Fix

- Logout() (#33) ([`5595e39`](https://github.com/chemelli74/aiocomelit/commit/5595e3996fc9fbca4a15c3ed5e92293d6604c3a1))


## v0.1.0 (2023-10-06)

### Feature

- Add irrigation and scenario devices (#29) ([`fd8c461`](https://github.com/chemelli74/aiocomelit/commit/fd8c46159af2c381bbe96c9c4a498b2d911cc31c))


### Unknown

## v0.0.9 (2023-09-25)

### Fix

- Improve login with pin (#25) ([`87951b7`](https://github.com/chemelli74/aiocomelit/commit/87951b73447e866a92ca2cf4cbc94dcc2126bfb6))


## v0.0.8 (2023-09-22)

### Fix

- Logging level (#24) ([`8464f94`](https://github.com/chemelli74/aiocomelit/commit/8464f94bd347a75b672c3abf30540b1bea291610))


## v0.0.7 (2023-09-22)

### Fix

- Login (and code optimization) (#23) ([`cd16d40`](https://github.com/chemelli74/aiocomelit/commit/cd16d40848285cd24faa8f7ed81d872b338d3848))


### Build

- Prepare changes for pre-commit autoupdate (#20) ([`36f2708`](https://github.com/chemelli74/aiocomelit/commit/36f270816981458ec8f85ca17fd66f1f175acf39))
- Fix poetry lock hook (#19) ([`572723c`](https://github.com/chemelli74/aiocomelit/commit/572723cba4f832911837910fc07bd493a4fcabe9))
- Pre-commit autoupdate, labels permissions (#18) ([`7bc48d9`](https://github.com/chemelli74/aiocomelit/commit/7bc48d9ca9525f8fb012731a96b1f72b0812a44c))


## v0.0.6 (2023-09-05)

### Fix

- Labels (#10) ([`e903a8c`](https://github.com/chemelli74/aiocomelit/commit/e903a8c5782995bc2f5b187778d48c002236b4a9))


## v0.0.5 (2023-07-19)

### Unknown

### Fix

- Commlint ([`1b1e836`](https://github.com/chemelli74/aiocomelit/commit/1b1e836b9b6f6f21999e2499af1d15c995e4cd7d))

