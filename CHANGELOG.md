# Changelog

## v1.0.0 (2025-05-26)

## v0.12.3 (2025-05-19)

### Bug fixes

- Not all modules installed ([`304aaf3`](https://github.com/chemelli74/aiocomelit/commit/304aaf3440f47e5a0de614ec8c704301714ef3a2))


### Refactoring

- Improve typing ([`0cedce6`](https://github.com/chemelli74/aiocomelit/commit/0cedce63889d4c76c44b8b15c11b762636955d18))


## v0.12.2 (2025-05-18)

### Bug fixes

- Handle old bridges that respond with empty data - follow up of #266 ([`5dba87f`](https://github.com/chemelli74/aiocomelit/commit/5dba87fff79059a98312f63ecd9b53c9ee1c4ead))


### Refactoring

- Improve logging ([`7343e96`](https://github.com/chemelli74/aiocomelit/commit/7343e9645a4e0375d460d0d1e8e6d237b89dba54))
- Make host internal ([`a4c0d6e`](https://github.com/chemelli74/aiocomelit/commit/a4c0d6e7047a377ebec8cb953db5f8fccfdd9bd0))
- Align timeout type to latest aiohttp ([`403d9f7`](https://github.com/chemelli74/aiocomelit/commit/403d9f7e2a1b10b1739433b6d649ce6aa9e72567))


## v0.12.1 (2025-05-11)

### Bug fixes

- Handle old bridges that respond with empty data ([`5cfdf5b`](https://github.com/chemelli74/aiocomelit/commit/5cfdf5b4cdf56fff43d01426d9acc28eddc8aefc))


## v0.12.0 (2025-04-24)

### Features

- Pass clientsession(aiohttp) as parameter ([`42e2c29`](https://github.com/chemelli74/aiocomelit/commit/42e2c297c7e601455278b5cedc486d2383ab9491))


### Build system

- Improve environment ([`8913356`](https://github.com/chemelli74/aiocomelit/commit/8913356dcd8424860b9e9732b449e9d8f418e277))


## v0.11.3 (2025-03-25)

### Bug fixes

- Typing for armed (comelitvedoareaobject) ([`e0935d2`](https://github.com/chemelli74/aiocomelit/commit/e0935d203278f22357ea29ff115bbc6a2cda09cc))


## v0.11.2 (2025-03-03)

### Bug fixes

- Get_all_areas_and_zones return type ([`3a1e112`](https://github.com/chemelli74/aiocomelit/commit/3a1e1128d4110a7430147cfa3129f59d0f90014d))


## v0.11.1 (2025-03-01)

### Bug fixes

- Improve typing ([`b479203`](https://github.com/chemelli74/aiocomelit/commit/b4792033b170a071a8b588a1293bc0d649387a5c))


## v0.11.0 (2025-02-18)

### Features

- Add vedo connection via bridge ([`9a72c2a`](https://github.com/chemelli74/aiocomelit/commit/9a72c2a933176dc7f2b883dee829f73425734319))


### Build system

- Update ruff rules ([`47d591f`](https://github.com/chemelli74/aiocomelit/commit/47d591fb02cd9e2458e195a3b1057bc9ee4c726a))


### Documentation

- Add library_test info ([`eb22380`](https://github.com/chemelli74/aiocomelit/commit/eb223805a28356c74a2245b174983a96dee710f2))


### Testing

- Use boolean argument ([`528dc4b`](https://github.com/chemelli74/aiocomelit/commit/528dc4be85d20281c48aea1e896b4c9f10facd70))
- Fix library_test ([`e9574fe`](https://github.com/chemelli74/aiocomelit/commit/e9574fe00e552502211522ee4812d2f99c70bc86))


## v0.10.1 (2024-12-29)

### Bug fixes

- Logging level ([`e15b2d4`](https://github.com/chemelli74/aiocomelit/commit/e15b2d4550c08e2f0e752acc451077b8db99716c))


### Unknown

### Testing

- Cleanup .coveragerc (again) ([`15328cd`](https://github.com/chemelli74/aiocomelit/commit/15328cdc4913912a59345bca59576def0f4bab22))


## v0.10.0 (2024-11-01)

### Build system

- Revert to standard semantic release ([`7c41119`](https://github.com/chemelli74/aiocomelit/commit/7c411191f6675e4a8467dccb2963f76ef010fbe9))
- Migrate-config ([`5486ffa`](https://github.com/chemelli74/aiocomelit/commit/5486ffa15817c6fb57cec5df8cc52fb812b2ea23))
- Add commitlint to pre-commit ([`26d0c17`](https://github.com/chemelli74/aiocomelit/commit/26d0c17759835ed69cf9c8cec1447f134c966264))


### Testing

- Cleanup .coveragerc ([`3bc5782`](https://github.com/chemelli74/aiocomelit/commit/3bc578221e8b5e5354f7ab66025a37ca19aa636a))


### Bug fixes

- Fix license classifier ([`fdfbec9`](https://github.com/chemelli74/aiocomelit/commit/fdfbec9f2ca1feea4c4eb2ec8752eebf0e3ea53e))


### Features

- Drop python 3.11 support ([`72c1ecf`](https://github.com/chemelli74/aiocomelit/commit/72c1ecf81a23b38c35b89b4a1484cf33371de848))


## v0.9.1 (2024-06-30)

### Bug fixes

- Fix licensing classifier ([`3000743`](https://github.com/chemelli74/aiocomelit/commit/3000743b3779be01ffa121cff043900338a07468))


### Build system

- Minor updates ([`1e8316d`](https://github.com/chemelli74/aiocomelit/commit/1e8316da680062cc23d0dbf82d855af675b5923a))
- Use ruff instead of isort, black, flake8, bandit and some pre-… ([`8bcf252`](https://github.com/chemelli74/aiocomelit/commit/8bcf25250632e8bfd755460d3840bf731b52774e))


## v0.9.0 (2024-02-23)

### Features

- Add humidity management ([`1f7b9a9`](https://github.com/chemelli74/aiocomelit/commit/1f7b9a9e6b0c333bc7311c1e2a8fd40288e28394))


### Build system

- Revert config change for actions/checkout@v4 ([`0235b7c`](https://github.com/chemelli74/aiocomelit/commit/0235b7c935abf32c2dacc7b2265054a5b65d126d))


## v0.8.3 (2024-02-05)

### Bug fixes

- Queue clima calls ([`90ea471`](https://github.com/chemelli74/aiocomelit/commit/90ea4712beab163ea28de018524972761b176be7))


## v0.8.2 (2024-01-25)

### Bug fixes

- Move math to library ([`91a1a29`](https://github.com/chemelli74/aiocomelit/commit/91a1a2926eb245323617f3b72c1cd1b1adc44b5d))


## v0.8.1 (2024-01-25)

### Bug fixes

- Move set_clima_status to the correct api ([`28848c8`](https://github.com/chemelli74/aiocomelit/commit/28848c8944c9031ba84afc83b5510415be8f33ec))


## v0.8.0 (2024-01-25)

### Features

- Clima set status ([`58e1691`](https://github.com/chemelli74/aiocomelit/commit/58e1691929e25dad26d267c91ff80e8655f10f39))


### Refactoring

- Library_test.py params via json config file ([`0f46014`](https://github.com/chemelli74/aiocomelit/commit/0f4601449609e9e4b606008c433e40ad81f8b5b1))


## v0.7.5 (2024-01-25)

### Bug fixes

- Improve vedo config retrieval ([`3cf6a49`](https://github.com/chemelli74/aiocomelit/commit/3cf6a499714c42173c8c985043eb7a68731dd9d9))


## v0.7.4 (2024-01-22)

### Bug fixes

- Check session active on logout and close ([`0bda7c9`](https://github.com/chemelli74/aiocomelit/commit/0bda7c9980794f5cc77add854f9a1cf50d517b21))


### Build system

- Use fork to force python 3.11 ([`7c4540a`](https://github.com/chemelli74/aiocomelit/commit/7c4540a99484a6f2a237aff1904b9639cba642ed))
- Update semantic-release to 8.x ([`cdb720f`](https://github.com/chemelli74/aiocomelit/commit/cdb720ff504603b00afe4fca435e6b3ffc8437d9))
- Switch ci to python 3.11 ([`b5ac23e`](https://github.com/chemelli74/aiocomelit/commit/b5ac23ec862f01f29643c00175878d78b793e99d))


## v0.7.3 (2024-01-10)

### Bug fixes

- Not logged in edge cases ([`4363dbb`](https://github.com/chemelli74/aiocomelit/commit/4363dbb54d90f5a4fc77a2be17f0df8ef121a09a))


## v0.7.2 (2024-01-10)

### Bug fixes

- Handle notlogged sporadic status ([`92e5663`](https://github.com/chemelli74/aiocomelit/commit/92e56636d15f95fbbb26011331d53a31938c003d))


## v0.7.1 (2024-01-10)

### Bug fixes

- Improve cookies handling ([`fdf3bb5`](https://github.com/chemelli74/aiocomelit/commit/fdf3bb52173e6a9888d23b877c925c285676c3bb))


## v0.7.0 (2023-12-16)

### Features

- Make login a shared method ([`4862904`](https://github.com/chemelli74/aiocomelit/commit/4862904880eb6d73677f90e7f9a9e74e65d73368))


## v0.6.2 (2023-11-28)

### Bug fixes

- Close session only if available ([`2acca97`](https://github.com/chemelli74/aiocomelit/commit/2acca97ee3d92ae8bba9c6481ad4461398ccfd21))


## v0.6.1 (2023-11-28)

### Bug fixes

- Recreate closed aiohttp session ([`98dc8bc`](https://github.com/chemelli74/aiocomelit/commit/98dc8bc3d0bda3c95e4ea2476b32f52e94528473))


## v0.6.0 (2023-11-16)

### Features

- More alarm data and code cleanup ([`abddf2a`](https://github.com/chemelli74/aiocomelit/commit/abddf2a3e0ddef609c6461b59d5ee6a49a6d7ecd))


## v0.5.2 (2023-11-13)

### Bug fixes

- Disk i/o pint should run in executor ([`ad95ade`](https://github.com/chemelli74/aiocomelit/commit/ad95ade1aa6ad94f2433a1c80f828792ce0f6689))


## v0.5.1 (2023-11-13)

### Bug fixes

- Timestamp strftime for windows ([`1afe620`](https://github.com/chemelli74/aiocomelit/commit/1afe6208e3f0acfd370a8f38c52ae48da5064226))


## v0.5.0 (2023-11-10)

### Features

- Improve performances ([`e4f65cb`](https://github.com/chemelli74/aiocomelit/commit/e4f65cba64e570b0e17e4907f7b7c955c4b0195d))


## v0.4.0 (2023-11-09)

### Features

- Add more logging ([`70347fe`](https://github.com/chemelli74/aiocomelit/commit/70347fe92c3f315a4935aad71c8111891ac7b80a))


## v0.3.2 (2023-11-09)

### Bug fixes

- Alarm management ([`64da301`](https://github.com/chemelli74/aiocomelit/commit/64da301ffade967b99f9e8ad750a0363bc23d0a8))


## v0.3.1 (2023-11-05)

### Bug fixes

- Updated headers for new fw versions ([`1dd99c4`](https://github.com/chemelli74/aiocomelit/commit/1dd99c441f91bf28c83a0fa39ac5f46c38d915ae))


## v0.3.0 (2023-10-17)

### Features

- Alarm vedo full support ([`61b6ac2`](https://github.com/chemelli74/aiocomelit/commit/61b6ac2ab38a1ff79a40b7214c2425fd14577380))


## v0.2.0 (2023-10-07)

### Features

- Add http port parametrization ([`49540a2`](https://github.com/chemelli74/aiocomelit/commit/49540a298e10b502f159c638918d610a26194348))


## v0.1.2 (2023-10-07)

### Bug fixes

- Variable in _login() ([`9820838`](https://github.com/chemelli74/aiocomelit/commit/9820838d95cd925c803150f0b3559058a6b8e08c))


## v0.1.1 (2023-10-07)

### Bug fixes

- Logout() ([`5595e39`](https://github.com/chemelli74/aiocomelit/commit/5595e3996fc9fbca4a15c3ed5e92293d6604c3a1))


## v0.1.0 (2023-10-06)

### Features

- Add irrigation and scenario devices ([`fd8c461`](https://github.com/chemelli74/aiocomelit/commit/fd8c46159af2c381bbe96c9c4a498b2d911cc31c))


### Unknown

## v0.0.9 (2023-09-25)

### Bug fixes

- Improve login with pin ([`87951b7`](https://github.com/chemelli74/aiocomelit/commit/87951b73447e866a92ca2cf4cbc94dcc2126bfb6))


## v0.0.8 (2023-09-22)

### Bug fixes

- Logging level ([`8464f94`](https://github.com/chemelli74/aiocomelit/commit/8464f94bd347a75b672c3abf30540b1bea291610))


## v0.0.7 (2023-09-22)

### Bug fixes

- Login (and code optimization) ([`cd16d40`](https://github.com/chemelli74/aiocomelit/commit/cd16d40848285cd24faa8f7ed81d872b338d3848))


### Build system

- Prepare changes for pre-commit autoupdate ([`36f2708`](https://github.com/chemelli74/aiocomelit/commit/36f270816981458ec8f85ca17fd66f1f175acf39))
- Fix poetry lock hook ([`572723c`](https://github.com/chemelli74/aiocomelit/commit/572723cba4f832911837910fc07bd493a4fcabe9))
- Pre-commit autoupdate, labels permissions ([`7bc48d9`](https://github.com/chemelli74/aiocomelit/commit/7bc48d9ca9525f8fb012731a96b1f72b0812a44c))


## v0.0.6 (2023-09-05)

### Bug fixes

- Labels ([`e903a8c`](https://github.com/chemelli74/aiocomelit/commit/e903a8c5782995bc2f5b187778d48c002236b4a9))


## v0.0.5 (2023-07-19)

### Unknown

### Bug fixes

- Commlint ([`1b1e836`](https://github.com/chemelli74/aiocomelit/commit/1b1e836b9b6f6f21999e2499af1d15c995e4cd7d))
