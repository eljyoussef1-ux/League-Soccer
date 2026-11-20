# Build WebAssembly de League-Soccer

## Lancer la version compilée

Si tu as reçu l'archive de la build, décompresse-la. Dans le dossier extrait,
lance `python3 -m http.server 8000` et ouvre
[http://localhost:8000/gameplayfootball.html](http://localhost:8000/gameplayfootball.html).
Les quatre fichiers `gameplayfootball.*` doivent rester ensemble.

## Compiler et servir le jeu

Prérequis : Git, CMake 3.14 ou plus récent, Ninja, Python 3 et les en-têtes
de [Boost 1.86.0](https://archives.boost.io/release/1.86.0/source/).
Extraire Boost en dehors du dépôt et indiquer le dossier qui contient
`boost/signals2.hpp`. Le premier build télécharge les ports Emscripten.

Depuis la racine du dépôt, avec un dossier `emsdk` et Boost à côté du dépôt :

```bash
git clone https://github.com/emscripten-core/emsdk.git ../emsdk
../emsdk/emsdk install 4.0.23
../emsdk/emsdk activate 4.0.23
source ../emsdk/emsdk_env.sh
emcc --version

emcmake cmake -G Ninja -S . -B build-wasm \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_TESTING=OFF \
  -DGF_WASM_BOOST_ROOT="$PWD/../boost_1_86_0"

cmake --build build-wasm --parallel
python3 -m http.server 8000 --directory build-wasm
```

Ouvrir [http://localhost:8000/gameplayfootball.html](http://localhost:8000/gameplayfootball.html)
avec un navigateur doté de WebGL2 et de l’extension `EXT_color_buffer_float`.
Les quatre fichiers doivent être servis ensemble depuis le même dossier HTTP.

| Fichier | Rôle |
| --- | --- |
| `build-wasm/gameplayfootball.html` | Page contenant le canvas et l’état du chargement |
| `build-wasm/gameplayfootball.js` | Chargeur et interface entre le navigateur et le moteur |
| `build-wasm/gameplayfootball.wasm` | Moteur du jeu compilé |
| `build-wasm/gameplayfootball.data` | Ressources préchargées dans le système de fichiers virtuel |

## Essayer le FC Hors-jeu

Pour compiler la variante avec l'équipe parodique, relancer la configuration
ci-dessus en ajoutant `-DGF_WASM_PARODY_SQUAD=ON`, puis reconstruire le jeu.
Dans **Match rapide**, choisir le championnat **Parodie**, le **FC Hors-jeu**
et un adversaire d'un autre championnat.

Le onze titulaire comprend Lionel Pessi (meneur), Cristiano Gronaldo
(avant-centre), Lamine Pas Mal (milieu gauche) et Enzo Khalifa (milieu
central). Les notes ci-dessous sont les notes de base, avant la forme et la
fatigue en match.

| Joueur | Vitesse | Frappe | Passe | Dribble | Défense | Physique | Endurance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lionel Pessi | 87 | 92 | 93 | 97 | 36 | 65 | 76 |
| Cristiano Gronaldo | 90 | 97 | 77 | 86 | 40 | 89 | 87 |
| Lamine Pas Mal | 94 | 78 | 80 | 93 | 38 | 62 | 85 |
| Enzo Khalifa | 74 | 74 | 92 | 82 | 77 | 76 | 91 |

Le fichier `scripts/seed_parody_squad.py` convertit les notes sur 100 en
22 attributs exploités par le moteur de match. CMake écrit la base peuplée
dans le répertoire de compilation. La variante est jouable en match rapide
au clavier et utilise le système de composition existant.

## Audit du dépôt et adaptations

| Élément | Adaptation web |
| --- | --- |
| `CMakeLists.txt`, `sources.cmake`, `CMakeModules/` | CMake reste le point d’entrée. Le build web utilise les ports SDL2, SDL2_image (PNG/JPEG), SDL2_ttf, SDL2_gfx et SQLite3, ainsi que les en-têtes Boost. |
| `src/main.cpp`, `src/gametask.cpp`, `src/framework/scheduler.cpp` | Le navigateur appelle le planificateur par `emscripten_set_main_loop`. Le traitement par image est borné et les commandes des tâches s’exécutent sur le même thread. Le terrain procédural génère ses quatre sections séquentiellement. |
| `src/systems/graphics/rendering/`, `data/media/shaders/` | SDL2 crée un contexte OpenGL ES 3.0/WebGL2. Le chargement convertit les shaders existants en GLSL ES 3.00. Le rendu utilise des formats de texture et des transferts de buffers compatibles WebGL2. |
| `src/systems/audio/` | Le port utilise le moteur silencieux existant. |
| `data/media/`, `data/databases/`, `data/locale/`, `data/football.config` | Emscripten les précharge aux chemins attendus par le moteur, y compris les shaders, les modèles 3D, les polices et la base SQLite. |

## Limites de cette première version

- Son désactivé. Une adaptation d’OpenAL au navigateur nécessiterait de gérer
  l’activation de l’audio après une interaction utilisateur.
- Les modifications de configuration et les sauvegardes restent en mémoire
  pendant la session. La persistance entre deux chargements nécessiterait
  un montage IndexedDB et la synchronisation des écritures.
- La préparation d’un match et le rendu s’exécutent sur le thread de la page.
  Les performances varient selon le navigateur et le GPU.

## Validation

- Compilation et édition de liens réussies avec Emscripten 4.0.23. Les quatre
  fichiers ont été servis en HTTP et le module a passé `WebAssembly.validate`.
- Chromium avec WebGL2 et SwiftShader a chargé les ressources, affiché le
  menu et démarré un match rapide au clavier. Le terrain, les joueurs, leurs
  ombres et le tableau des scores ont été vérifiés en cours de rendu.
- Les 322 tests natifs sans interface passent. Le jeu de bureau complet,
  les autres navigateurs, les manettes et les modes carrière restent à
  vérifier pour cette version.
