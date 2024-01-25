# Changelog

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


### Chore

- Improve library error logging (#78) ([`d7ecd86`](https://github.com/chemelli74/aiocomelit/commit/d7ecd865646adbe2756f930269f52b3f80a7d4c8))


## v0.7.2 (2024-01-10)

### Fix

- Handle notlogged sporadic status (#74) ([`92e5663`](https://github.com/chemelli74/aiocomelit/commit/92e56636d15f95fbbb26011331d53a31938c003d))


## v0.7.1 (2024-01-10)

### Fix

- Improve cookies handling (#72) ([`fdf3bb5`](https://github.com/chemelli74/aiocomelit/commit/fdf3bb52173e6a9888d23b877c925c285676c3bb))


### Chore

- Pre-commit autoupdate (#75) ([`d79cf71`](https://github.com/chemelli74/aiocomelit/commit/d79cf71b4e208485892d540b3559b4edb812033e))
- Bump tiangolo/issue-manager from 0.4.0 to 0.4.1 (#77) ([`44ca53a`](https://github.com/chemelli74/aiocomelit/commit/44ca53a060985d03a8ad0b215cdc7540f71cc93d))
- Bump wagoid/commitlint-github-action from 5.4.4 to 5.4.5 (#76) ([`10c5746`](https://github.com/chemelli74/aiocomelit/commit/10c5746f15bbba7f81173d8f014c402c6431364b))
- Fix vs debug launch (#73) ([`e40eebd`](https://github.com/chemelli74/aiocomelit/commit/e40eebd50c75c1af7df5db09c40a18097814309b))
- Upgrade dependencies (#70) ([`3e1af1a`](https://github.com/chemelli74/aiocomelit/commit/3e1af1abd8567e180590ed8b76f83908e507a8f7))
- Bump pytest from 7.4.3 to 7.4.4 (#69) ([`7c6338a`](https://github.com/chemelli74/aiocomelit/commit/7c6338adcb407b6b1976278058d2c11bec6086ca))
- Pre-commit autoupdate (#68) ([`7e9aca4`](https://github.com/chemelli74/aiocomelit/commit/7e9aca42dd6f2f0c5358f748169c197c8c045d33))


## v0.7.0 (2023-12-16)

### Feature

- Make login a shared method (#64) ([`4862904`](https://github.com/chemelli74/aiocomelit/commit/4862904880eb6d73677f90e7f9a9e74e65d73368))


### Chore

- Pre-commit autoupdate (#63) ([`727753f`](https://github.com/chemelli74/aiocomelit/commit/727753fb67af5de3f88dcbd767b3fbd32e868c3e))
- Bump pint from 0.22 to 0.23 (#67) ([`fcafb28`](https://github.com/chemelli74/aiocomelit/commit/fcafb288d0f1c2b670e5d4788d1fccf17be03e83))
- Bump actions/setup-python from 4 to 5 (#66) ([`ac0a69b`](https://github.com/chemelli74/aiocomelit/commit/ac0a69ba5e0eb9eec881b9582ae3f742caaed962))
- Upgrade dependencies (#61) ([`8afb2e2`](https://github.com/chemelli74/aiocomelit/commit/8afb2e26147e5c4b40242c628ea252561da5f954))
- Bump colorlog from 6.7.0 to 6.8.0 (#62) ([`457b14b`](https://github.com/chemelli74/aiocomelit/commit/457b14b5c61c1a6315ddcae6ddae2ab97e732851))


## v0.6.2 (2023-11-28)

### Fix

- Close session only if available (#60) ([`2acca97`](https://github.com/chemelli74/aiocomelit/commit/2acca97ee3d92ae8bba9c6481ad4461398ccfd21))


## v0.6.1 (2023-11-28)

### Fix

- Recreate closed aiohttp session (#57) ([`98dc8bc`](https://github.com/chemelli74/aiocomelit/commit/98dc8bc3d0bda3c95e4ea2476b32f52e94528473))


### Chore

- Bump aiohttp from 3.8.6 to 3.9.0 (#56) ([`ac38182`](https://github.com/chemelli74/aiocomelit/commit/ac3818299a5a7369c3df501b178f97348d45b048))
- Pre-commit autoupdate (#59) ([`1e30159`](https://github.com/chemelli74/aiocomelit/commit/1e301595c3affbea1e035868f3e02eaee1e91c39))


## v0.6.0 (2023-11-16)

### Feature

- More alarm data and code cleanup (#52) ([`abddf2a`](https://github.com/chemelli74/aiocomelit/commit/abddf2a3e0ddef609c6461b59d5ee6a49a6d7ecd))


### Chore

- Pre-commit autoupdate (#55) ([`c8f6c8c`](https://github.com/chemelli74/aiocomelit/commit/c8f6c8c1395685dee91ff9ccfe368e46742e9343))


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


### Chore

- Allow vscode to find poetry interpreter (#48) ([`57448f9`](https://github.com/chemelli74/aiocomelit/commit/57448f9cf1e6977621b36e691af49d4d04aacf36))
- Pre-commit autoupdate (#47) ([`465590a`](https://github.com/chemelli74/aiocomelit/commit/465590af43943a268ec94a54c79c7ce88f623198))


## v0.3.1 (2023-11-05)

### Fix

- Updated headers for new fw versions (#46) ([`1dd99c4`](https://github.com/chemelli74/aiocomelit/commit/1dd99c441f91bf28c83a0fa39ac5f46c38d915ae))


### Chore

- Upgrade dependencies (#44) ([`2f728df`](https://github.com/chemelli74/aiocomelit/commit/2f728dfbe7bdedf072dfd2cd93c90b76fc742417))
- Bump wagoid/commitlint-github-action from 5.4.3 to 5.4.4 (#45) ([`c991f38`](https://github.com/chemelli74/aiocomelit/commit/c991f383cb1eedf00905b6b94842604045da8282))
- Bump pytest from 7.4.2 to 7.4.3 (#43) ([`c695780`](https://github.com/chemelli74/aiocomelit/commit/c6957804f2fe0c15d388693f06bdf4649b3cf3ae))
- Pre-commit autoupdate (#42) ([`bde4cdb`](https://github.com/chemelli74/aiocomelit/commit/bde4cdb10db5de326815023ff1ea5b5e3b12f081))


## v0.3.0 (2023-10-17)

### Feature

- Alarm vedo full support (#39) ([`61b6ac2`](https://github.com/chemelli74/aiocomelit/commit/61b6ac2ab38a1ff79a40b7214c2425fd14577380))


### Chore

- Pre-commit autoupdate (#41) ([`a580ee7`](https://github.com/chemelli74/aiocomelit/commit/a580ee76492850206eec5450d25cf38a65f959d5))
- Add param for enable/disable tests (#38) ([`b81c324`](https://github.com/chemelli74/aiocomelit/commit/b81c324e9945d2fc378696a0b6350e48c38e554b))
- Code quality (#37) ([`0fb87da`](https://github.com/chemelli74/aiocomelit/commit/0fb87da03729775e4f89250d32f06ddebd82da28))
- Pre-commit autoupdate (#36) ([`ea4d3a9`](https://github.com/chemelli74/aiocomelit/commit/ea4d3a95027ced09e19a43532a340337eb241145))
- Bump aiohttp from 3.8.5 to 3.8.6 (#35) ([`176fe8b`](https://github.com/chemelli74/aiocomelit/commit/176fe8b5b16a5ebb6bf59c12be19ddb775df0cf2))


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


### Chore

- Pre-commit autoupdate (#31) ([`f03f5f3`](https://github.com/chemelli74/aiocomelit/commit/f03f5f3c0d87ffb1d5ad2071bcd7ecaca0e61ad4))
- Upgrade dependencies (#30) ([`df5a66d`](https://github.com/chemelli74/aiocomelit/commit/df5a66d0fa7a8814c6a13b7ba6657ead1b675dbf))
- Pre-commit autoupdate (#26) ([`795cb5f`](https://github.com/chemelli74/aiocomelit/commit/795cb5f1a96ba655f9cf934a9b777d6624257a86))


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


### Chore

- Code reorg (#22) ([`b6c5204`](https://github.com/chemelli74/aiocomelit/commit/b6c5204bc11224fb1138ea707f91bd8e6c9503d9))
- Pre-commit autoupdate (#21) ([`55eff97`](https://github.com/chemelli74/aiocomelit/commit/55eff97b22f0f66dc95c48a0d1a12faa71e20f95))
- Bump actions/checkout from 3 to 4 (#14) ([`9a75ebc`](https://github.com/chemelli74/aiocomelit/commit/9a75ebcb17af596e928ce8bebfce43dde597ca3a))
- Bump pytest-cov from 3.0.0 to 4.1.0 (#17) ([`d1fe93d`](https://github.com/chemelli74/aiocomelit/commit/d1fe93ddbd6eb8c0abb345cdda963298d8e4abea))
- Bump wagoid/commitlint-github-action from 5.4.1 to 5.4.3 (#13) ([`c14e078`](https://github.com/chemelli74/aiocomelit/commit/c14e078d38a11dd4acba0d055f31129430699297))
- Bump pytest from 7.4.1 to 7.4.2 (#16) ([`a6e2579`](https://github.com/chemelli74/aiocomelit/commit/a6e25791af3682760a06b2f371c3000273335dfe))
- Bump snok/install-poetry from 1.3.3 to 1.3.4 (#12) ([`56c88be`](https://github.com/chemelli74/aiocomelit/commit/56c88be4d0e6befd1ec251d38b52b41a28a1cfb4))
- Add dependabot (#11) ([`a0adc8d`](https://github.com/chemelli74/aiocomelit/commit/a0adc8d6b2bbc118611c1dd2c842a57963448a87))


### Build

- Prepare changes for pre-commit autoupdate (#20) ([`36f2708`](https://github.com/chemelli74/aiocomelit/commit/36f270816981458ec8f85ca17fd66f1f175acf39))
- Fix poetry lock hook (#19) ([`572723c`](https://github.com/chemelli74/aiocomelit/commit/572723cba4f832911837910fc07bd493a4fcabe9))
- Pre-commit autoupdate, labels permissions (#18) ([`7bc48d9`](https://github.com/chemelli74/aiocomelit/commit/7bc48d9ca9525f8fb012731a96b1f72b0812a44c))


## v0.0.6 (2023-09-05)

### Fix

- Labels (#10) ([`e903a8c`](https://github.com/chemelli74/aiocomelit/commit/e903a8c5782995bc2f5b187778d48c002236b4a9))


### Chore

- Pre-commit additional hooks (#9) ([`2e47359`](https://github.com/chemelli74/aiocomelit/commit/2e47359b54a160ede594857bdd399b570fc660b1))
- Upgrade dependencies (#8) ([`3bffe3e`](https://github.com/chemelli74/aiocomelit/commit/3bffe3e64a2b478713a84ad3f360c2421c707610))


## v0.0.5 (2023-07-19)

### Unknown

### Fix

- Commlint ([`1b1e836`](https://github.com/chemelli74/aiocomelit/commit/1b1e836b9b6f6f21999e2499af1d15c995e4cd7d))


### Chore

- Version bump (#6) ([`a340137`](https://github.com/chemelli74/aiocomelit/commit/a340137cd4dceab3e44200bc3ce88def4544f0f8))
- Login and devices status (#5) ([`71d944e`](https://github.com/chemelli74/aiocomelit/commit/71d944e50123e42edd044b7fe8b9488b7e81b264))
- Expose light and cover functions (#4) ([`e1143eb`](https://github.com/chemelli74/aiocomelit/commit/e1143eb51fee1596cb4b3828899d42a619139e78))
- Initial commit ([`81edef7`](https://github.com/chemelli74/aiocomelit/commit/81edef7dac9a0a09c79b7517358d2399587bf7a1))
