[![pipeline status](https://git.fh-muenster.de/masterprojekt-mls/implementation/badges/master/pipeline.svg)](https://git.fh-muenster.de/masterprojekt-mls/implementation/commits/master)
[![coverage report](https://git.fh-muenster.de/masterprojekt-mls/implementation/badges/master/coverage.svg)](https://git.fh-muenster.de/masterprojekt-mls/implementation/commits/master)


(Der Coveragewert ist das Arithmetische Mittel aus allen Coveragewerten, siehe [hier](https://gitlab.com/gitlab-org/gitlab-ce/issues/22158))
# MLS Umsetzung

Dieses Repository vereint sowohl die Implementierung von MLS als [Chatprotokoll](https://datatracker.ietf.org/doc/draft-ietf-mls-protocol/),
als auch eine Umsetzung von Tooling, das notwendig ist um einen Chatserver auf dem Protokoll zu
betreiben (vgl [draft-ietf-mls-architecture](https://datatracker.ietf.org/doc/draft-ietf-mls-architecture/)).

## Build Artefakte

Für freundliche Projektbetreuer stellt dieses Projekt (dank CI) Buildartefakte zum
direkten Download zur Verfügung, sodass kein keine Dev-Umgebung aufgesetzen werden muss.

### Download
** WORK IN PROGRESS **

### Using this Software
** WORK IN PROGRESS **

## Development

### Tooling
#### Nix
Dieses Projekt nutzt das [Nix Build Tool](https://nixos.org/nix/). Um das Projekt zu bauen,
muss lediglich `nix-build` eingegeben werden. Üblicherweise reicht zur Installation ein `curl https://nixos.org/nix/install | sh`

##### Installationshinweis für Arch Nutzer
Bei Installationsfehler "Clone Operation not permitted":
https://github.com/NixOS/nix/issues/2633

Wenn nix-* Befehle nach Installationnicht verfügbar sind:
https://github.com/NixOS/nix/issues/879#issuecomment-410904367

#### Git Workflow
Pushes auf den Master sind in diesem Projekt verboten. Um eine Änderung einzureichen, musst
ihr eure Änderungen auf einem neuen Branch einpflegen und von dort einen Pull-Request stellen.

Um einen PR zu mergen braucht ihr {ein|zwei} Approve von anderen Teammitgliedern. Merges
sind nur möglich, wenn die [CI](#CI) grün ist.

Nachdem ein PR gemerged wurde, verwendet bitte den feature-branch nicht weiter, sondern
erstellt einen neuen Branch. Es gilt _ein feature je branch_. 

**WICHTIG WICHTIG** 
Sollte sich der Masterstand während der Laufzeit eures Branches ändern, **merged** nicht
den master stand in ihn rein um ihn zu updaten, sondern **rebased** ihn, also
`git pull --rebase origin master` auf eurem Branch. 

Bitte merged keine _Kaffeepausen_-Commits in den Master und gebt Ihnen sinnvolle Commitmassages 
auf **DEUTSCH**. Auf euren Dev-Branches kann eure History aussehen wie sie will, ihr solltet sie
nur mittels eines `git rebase -i HEAD~n`, mit `n` als Commit-Anzahl in eurem Branch, vor einem Merge
umschreiben.

#### CI

Dieses Projekt nutzt CI. Bei jedem Pull request wird die Software gebaut, alle Tests sowie
der [Linter](#Linter) ausgeführt. 

#### Linter

Da in diesem Projekt Leute mit sehr diversen Background mitarbeiten, wird ein Linter genutzt 
um einen gemeinsamen Codestyle zu erreichen, den jeder gut lesen kann. Im Falle der Python-Projekte 
ist dies `pylint`, für Rust folgt bald noch einer.

## Projektstruktur

```
.
├── infrastructure
│   ├── authserver
│   ├── chatclient
│   ├── dirserver
│   │   ├── dirserver
│   │   └── tests
│   └── tests
└── libMLS
    
```

`libMLS`: Implementierung von MLS in Rust

`infrastructure`: 
- `authserver`: Implementierung des AS 
- `dirserver`: Implementierung des Directory Servers
- `chatclient`: Ein MLS Chat client mit GUI
- `tests`: Globale (Integration-)Tests für alle Infrastruktur projekte


