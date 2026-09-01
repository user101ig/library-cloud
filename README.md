# Library Cloud

Το Library Cloud είναι ένα πρωτότυπο σύστημα διαχείρισης βιβλιοθήκης που
συνδυάζει μία web εφαρμογή με υπηρεσίες authentication, messaging, workflow
automation και object storage. Στόχος του project δεν είναι μόνο η καταχώριση
βιβλίων και δανεισμών, αλλά η παρουσίαση μιας ολοκληρωμένης cloud αρχιτεκτονικής
στην οποία ανεξάρτητες υπηρεσίες συνεργάζονται αυτόματα.

Όλοι οι λογαριασμοί, οι κωδικοί και τα URLs του demo περιλαμβάνονται στην
ενότητα [Credentials](#credentials).

## Περιεχόμενα

1. [Επιχειρησιακή περιγραφή](#επιχειρησιακή-περιγραφή)
2. [Βασικές λειτουργίες](#βασικές-λειτουργίες)
3. [Αρχιτεκτονική](#αρχιτεκτονική)
4. [Τεχνολογίες και επιλογές](#τεχνολογίες-και-επιλογές)
5. [Δομή του project](#δομή-του-project)
6. [Δομή της εφαρμογής](#δομή-της-εφαρμογής)
7. [Σχήμα βάσης δεδομένων](#σχήμα-βάσης-δεδομένων)
8. [Authentication και authorization](#authentication-και-authorization)
9. [Keycloak](#keycloak)
10. [Credentials](#credentials)
11. [RabbitMQ](#rabbitmq)
12. [Node-RED](#node-red)
13. [MinIO και PDF αναφορές](#minio-και-pdf-αναφορές)
14. [Docker Compose](#docker-compose)
15. [Αναλυτική τοπική εγκατάσταση](#αναλυτική-τοπική-εγκατάσταση)
16. [Τοπική ανάπτυξη με uv](#τοπική-ανάπτυξη-με-uv)
17. [Kubernetes](#kubernetes)
18. [Σενάριο παρουσίασης](#σενάριο-παρουσίασης)
19. [Αντιμετώπιση προβλημάτων](#αντιμετώπιση-προβλημάτων)
20. [Ασφάλεια και περιορισμοί](#ασφάλεια-και-περιορισμοί)
21. [Κάλυψη τεχνολογιών εργασίας](#κάλυψη-τεχνολογιών-εργασίας)

## Επιχειρησιακή περιγραφή

Το σύστημα απευθύνεται σε βιβλιοθήκες που χρειάζονται μία απλή εφαρμογή για:

- διαχείριση του καταλόγου βιβλίων,
- εγγραφή μελών,
- καταγραφή δανεισμών και επιστροφών,
- έλεγχο διαθέσιμων αντιτύπων,
- διαχωρισμό δικαιωμάτων ανά ρόλο,
- αυτόματη παραγωγή αποδεικτικών PDF,
- διατήρηση αρχείου ενεργειών εκτός της κύριας βάσης.

Όταν πραγματοποιείται ένας δανεισμός ή μία επιστροφή, η βασική λειτουργία
ολοκληρώνεται άμεσα στη βάση. Στη συνέχεια δημοσιεύεται ένα event, το οποίο
επεξεργάζεται ανεξάρτητα το Node-RED και μετατρέπει σε PDF αναφορά στο MinIO.
Με αυτόν τον τρόπο η παραγωγή αναφοράς δεν επιβαρύνει το HTTP request του
χρήστη και μπορεί να εξελιχθεί ανεξάρτητα από την κύρια εφαρμογή.

## Βασικές λειτουργίες

- Είσοδος και έξοδος χρηστών μέσω Keycloak.
- Server-side session με `HttpOnly` cookie.
- Προβολή και προσθήκη βιβλίων ανάλογα με τον ρόλο.
- Δημιουργία και προβολή μελών.
- Δανεισμός διαθέσιμου βιβλίου και επιστροφή ενεργού δανεισμού.
- Αυτόματη ενημέρωση διαθέσιμων αντιτύπων.
- Απόρριψη δανεισμού όταν δεν υπάρχει διαθέσιμο αντίτυπο.
- Δημοσίευση `loan.borrowed` και `loan.returned` events.
- Αυτόματη δημιουργία και αρχειοθέτηση PDF στο MinIO.

## Αρχιτεκτονική

```mermaid
flowchart LR
    U[Χρήστης / Browser]
    API[FastAPI + HTMX]
    KC[Keycloak]
    DB[(SQLite)]
    RMQ[(RabbitMQ)]
    NR[Node-RED]
    MIO[(MinIO)]

    U -->|HTTP / HTML| API
    API <-->|Authorization Code + PKCE| KC
    API <-->|SQLAlchemy| DB
    API -->|loan events| RMQ
    RMQ -->|loan.#| NR
    NR -->|PDF receipts| MIO
```

Υπάρχουν δύο είδη επικοινωνίας:

- **Synchronous:** Browser, FastAPI, Keycloak και SQLite. Ο χρήστης περιμένει
  άμεση απάντηση.
- **Asynchronous:** FastAPI, RabbitMQ, Node-RED και MinIO. Η δημιουργία PDF
  πραγματοποιείται στο background μετά την ολοκλήρωση του δανεισμού.

## Τεχνολογίες και επιλογές

### FastAPI

Το FastAPI αποτελεί το backend και εκθέτει REST endpoints και HTMX routes.
Επιλέχθηκε για τα type hints, το dependency injection, το OpenAPI και την
άμεση συνεργασία με Pydantic.

### HTMX και Jinja2

Το frontend δεν είναι ξεχωριστή εφαρμογή. Το Jinja2 δημιουργεί HTML στον
server και το HTMX ενημερώνει μόνο το απαραίτητο τμήμα της σελίδας. Έτσι δεν
χρειάζεται δεύτερο frontend project, το authentication παραμένει στο backend
και τα Keycloak tokens δεν αποθηκεύονται στον browser.

### SQLAlchemy και SQLite

Το SQLAlchemy χρησιμοποιείται ως ORM και χωρίζει τα queries από τους business
rules. Η SQLite είναι αρκετή για το εκπαιδευτικό prototype, δεν χρειάζεται
ξεχωριστό database server και αποθηκεύεται σε persistent file.

### Keycloak

Το Keycloak διαχειρίζεται χρήστες, passwords, roles και OpenID Connect. Η
εφαρμογή δεν υλοποιεί δικό της password storage και δεν βλέπει το password του
χρήστη.

### RabbitMQ

Το RabbitMQ λειτουργεί ως message broker. Αποσυνδέει τον δανεισμό από τη
δημιουργία PDF και επιτρέπει σε νέους consumers να αντιδράσουν στα ίδια events.

### Node-RED

Το Node-RED εκτελεί το background workflow χωρίς δεύτερο custom backend
service. Καταναλώνει events, δημιουργεί PDF και τα ανεβάζει στο MinIO.

### MinIO

Το MinIO είναι S3-compatible object storage. Τα PDF είναι αρχεία/objects και
όχι σχεσιακά δεδομένα, επομένως αποθηκεύονται χωριστά από τη SQLite.

### Docker Compose

Το Docker Compose είναι ο βασικός τρόπος εκτέλεσης. Χτίζει τα custom images,
δημιουργεί δίκτυο και volumes, εκτελεί health checks και ξεκινά όλο το σύστημα
με μία εντολή.

### Kubernetes

Τα manifests αποτελούν δεύτερο τρόπο deployment και παρουσιάζουν orchestration,
service discovery, probes, configuration και persistent storage. Για το απλό
local demo προτιμάται το Docker Compose.

## Δομή του project

```text
.
├── app/                    FastAPI εφαρμογή και HTMX frontend
├── data/                   Ενεργό SQLite αρχείο
├── keycloak/               Realm import και custom login theme
├── node-red/               Custom image και αυτοματοποιημένο flow
├── k8s/                    Kubernetes manifests
├── Dockerfile              Image του FastAPI
├── docker-compose.yml      Πλήρες local environment
├── pyproject.toml          Python project και dependencies
├── uv.lock                 Κλειδωμένες Python εκδόσεις
├── .env.example            Παράδειγμα τοπικών ρυθμίσεων
└── README.md               Τεχνική τεκμηρίωση
```

### `keycloak/`

- `Dockerfile`: δημιουργεί αυτοτελές Keycloak image.
- `import/library-realm.json`: realm, client, roles και demo users.
- `themes/library/`: custom αγγλικό login theme.

### `node-red/`

- `Dockerfile`: εγκαθιστά `amqplib`, `minio` και `pdfkit`.
- `flows.json`: αποθηκευμένο και version-controlled workflow.
- `settings.js`: ενεργοποιεί external modules και ρυθμίζει τον editor.
- `package.json`: Node.js dependencies του flow.

### `k8s/`

- `00-namespace.yaml`: namespace `library-cloud`.
- `01-config.yaml`: ConfigMap και development Secret.
- `02-storage.yaml`: PersistentVolumeClaims.
- `10-keycloak.yaml`: Keycloak Deployment και Service.
- `11-rabbitmq.yaml`: RabbitMQ Deployment και Service.
- `12-minio.yaml`: MinIO Deployment και Service.
- `13-node-red.yaml`: Node-RED Deployment και Service.
- `14-api.yaml`: FastAPI Deployment και Service.

## Δομή της εφαρμογής

```text
app/
├── main.py
├── auth.py
├── database.py
├── errors.py
├── messaging.py
├── models.py
├── schemas.py
├── repositories/
│   ├── books.py
│   ├── members.py
│   └── loans.py
├── services/
│   ├── books.py
│   ├── members.py
│   └── loans.py
├── routers/
│   ├── auth.py
│   ├── books.py
│   ├── members.py
│   ├── loans.py
│   ├── health.py
│   └── ui.py
├── templates/
│   ├── index.html
│   └── partials/
└── static/app.css
```

- `main.py`: FastAPI app, startup, static files και routers.
- `auth.py`: PKCE, JWT validation, sessions, CSRF και roles.
- `database.py`: SQLAlchemy engine, sessions και δημιουργία tables.
- `models.py`: ORM μοντέλα `Book`, `Member` και `Loan`.
- `schemas.py`: validation request και response δεδομένων.
- `errors.py`: κοινά application exceptions.
- `messaging.py`: δημοσίευση RabbitMQ events.
- `repositories/`: αποκλειστικά database queries.
- `services/`: business rules και transactions.
- `routers/`: HTTP endpoints και role requirements.
- `templates/`: βασική σελίδα και HTMX partials.
- `static/app.css`: κοινό λιτό UI.

Ο διαχωρισμός Router → Service → Repository κρατά το HTTP layer, τους κανόνες
και τα queries ανεξάρτητα.

## Σχήμα βάσης δεδομένων

```mermaid
erDiagram
    BOOK ||--o{ LOAN : "δανείζεται"
    MEMBER ||--o{ LOAN : "πραγματοποιεί"

    BOOK {
        string id PK
        string title
        string author
        string isbn UK
        integer total_copies
        integer available_copies
        datetime created_at
    }
    MEMBER {
        string id PK
        string full_name
        string email UK
        datetime created_at
    }
    LOAN {
        string id PK
        string book_id FK
        string member_id FK
        string status
        datetime borrowed_at
        datetime returned_at
    }
```

### `books`

- `id`: UUID primary key.
- `title`, `author`: βασικά στοιχεία.
- `isbn`: προαιρετικό και μοναδικό.
- `total_copies`, `available_copies`: συνολικά και διαθέσιμα αντίτυπα.
- `created_at`: χρόνος δημιουργίας.

### `members`

- `id`: UUID primary key.
- `full_name`: όνομα μέλους.
- `email`: μοναδικό email.
- `created_at`: χρόνος εγγραφής.

### `loans`

- `id`: UUID primary key.
- `book_id`, `member_id`: foreign keys.
- `status`: μόνο `borrowed` ή `returned`.
- `borrowed_at`, `returned_at`: χρόνοι δανεισμού και επιστροφής.

Τα UUIDs χρησιμοποιούνται εσωτερικά ώστε τα resources να μην έχουν
προβλέψιμα αριθμητικά IDs. Δεν περιλαμβάνονται στα PDF ή στα MinIO filenames.

## Authentication και authorization

Χρησιμοποιείται Backend-for-Frontend. Ο browser δεν λαμβάνει access ή refresh
token. Τα tokens αποθηκεύονται στη μνήμη του FastAPI και ο browser λαμβάνει
μόνο ένα τυχαίο `HttpOnly` session cookie.

```mermaid
sequenceDiagram
    actor U as Χρήστης
    participant B as Browser
    participant API as FastAPI
    participant KC as Keycloak

    U->>B: Επιλέγει Sign in
    B->>API: GET /auth/login
    API->>API: State, verifier και PKCE challenge
    API-->>B: Redirect προς Keycloak
    B->>KC: Authorization request
    U->>KC: Username και password
    KC-->>B: Redirect με authorization code
    B->>API: GET /auth/callback
    API->>KC: Code + verifier + client secret
    KC-->>API: Access και refresh token
    API->>API: JWT validation και δημιουργία session
    API-->>B: HttpOnly session cookie
```

Το backend ελέγχει την RSA υπογραφή μέσω JWKS, τον issuer, το expiration, το
`sub`, το `azp` και τα realm roles. Για state-changing requests το frontend
στέλνει `X-CSRF-Token`, το οποίο συνδέεται με το server-side session.

Χρησιμοποιούνται δύο Keycloak URLs:

- `KEYCLOAK_PUBLIC_URL=http://localhost:8080`: browser redirects.
- `KEYCLOAK_INTERNAL_URL=http://keycloak:8080`: container-to-container calls.

## Keycloak

### Realm και client

- Realm: `library`
- Client: `library-api`
- Protocol: OpenID Connect
- Flow: Authorization Code with PKCE
- Client type: confidential
- Theme: `library`
- Γλώσσα theme: αγγλικά

### Ρόλοι και δικαιώματα

| Ενέργεια | Admin | Librarian | Reader |
| --- | :---: | :---: | :---: |
| Προβολή βιβλίων | Ναι | Ναι | Ναι |
| Προσθήκη βιβλίου | Ναι | Ναι | Όχι |
| Προβολή/δημιουργία μελών | Ναι | Ναι | Όχι |
| Προβολή δανεισμών | Ναι | Ναι | Όχι |
| Δανεισμός/επιστροφή | Ναι | Ναι | Όχι |

Τα δικαιώματα εφαρμόζονται στο backend με το dependency `require_roles()`.
Η απόκρυψη κουμπιών στο UI είναι μόνο ευκολία· η προστασία γίνεται πάντα στα
FastAPI endpoints.

## Credentials

Όλα τα παρακάτω credentials είναι σταθερές development τιμές για το τοπικό
demo και το Kubernetes deployment. Δεν προορίζονται για production χρήση.

### Χρήστες εφαρμογής

| Username | Password | Email | Roles |
| --- | --- | --- | --- |
| `test-admin` | `Admin123!` | `test-admin@library.local` | `admin` |
| `test-librarian` | `Librarian123!` | `test-librarian@library.local` | `librarian` |
| `test-reader` | `Reader123!` | `test-reader@library.local` | `reader` |

Η εφαρμογή δεν έχει ξεχωριστούς local users. Όλοι οι χρήστες ανήκουν στο
Keycloak realm `library`.

### Keycloak administration

| Ρύθμιση | Τιμή |
| --- | --- |
| Admin Console | `http://localhost:8080/admin/` |
| Admin username | `admin` |
| Admin password | `admin` |
| Realm | `library` |
| Client ID | `library-api` |
| Client secret | `library-api-dev-secret` |

### RabbitMQ

| Ρύθμιση | Τιμή |
| --- | --- |
| Management Console | `http://localhost:15672` |
| AMQP endpoint | `amqp://localhost:5672/` |
| Username | `library` |
| Password | `library` |
| Exchange | `library.events` |
| Queue | `library.node-red` |

### MinIO

| Ρύθμιση | Τιμή |
| --- | --- |
| Console | `http://localhost:9001` |
| S3 API | `http://localhost:9000` |
| Username / access key | `library` |
| Password / secret key | `library-minio` |
| Bucket | `library-audit` |
| PDF path | `loan-reports/YYYY/MM/DD/` |

### Node-RED

| Ρύθμιση | Τιμή |
| --- | --- |
| Flow editor | `http://localhost:1880` |
| Web login | Δεν υπάρχει στο local demo |
| Credential secret | `library-node-red-dev-secret` |

### SQLite

- Αρχείο Docker Compose: `data/library.db`
- Kubernetes path: `/app/data/library.db` στο PVC `api-data`
- Username/password: δεν χρησιμοποιούνται

### Εσωτερικές διευθύνσεις containers

| Service | Διεύθυνση |
| --- | --- |
| Keycloak | `http://keycloak:8080` |
| RabbitMQ | `amqp://library:library@rabbitmq:5672/` |
| MinIO | `http://minio:9000` |

Οι εσωτερικές διευθύνσεις χρησιμοποιούνται από τα containers και δεν ανοίγουν
από τον browser του host.

## RabbitMQ

Το FastAPI δημοσιεύει event μετά το επιτυχημένο database commit.

| Ρύθμιση | Τιμή |
| --- | --- |
| Exchange | `library.events` |
| Exchange type | `topic` |
| Queue | `library.node-red` |
| Binding | `loan.#` |
| Events | `loan.borrowed`, `loan.returned` |
| Durability | Durable exchange και queue |
| Message delivery | Persistent |

```json
{
  "type": "loan.borrowed",
  "occurred_at": "2026-08-28T10:00:00+00:00",
  "data": {
    "book_title": "Clean Code",
    "book_author": "Robert C. Martin",
    "member_name": "Demo Member"
  }
}
```

Δεν δημοσιεύονται UUIDs στο event. Αν το RabbitMQ είναι προσωρινά εκτός, το
πρόβλημα γράφεται στα logs αλλά δεν αναιρείται ο ήδη ολοκληρωμένος δανεισμός.

## Node-RED

```mermaid
flowchart LR
    Q[RabbitMQ queue<br/>library.node-red]
    C[Parse event]
    P[PDFKit<br/>Create receipt]
    B[Create bucket<br/>if missing]
    M[(MinIO<br/>library-audit)]
    D[Debug output]
    Q --> C --> P --> B --> M --> D
```

Κατά την εκκίνηση το flow συνδέεται στο RabbitMQ, δηλώνει το exchange,
δημιουργεί queue και binding, συνδέεται στο MinIO και δημιουργεί το bucket αν
λείπει. Για κάθε event κάνει JSON parsing, αναγνωρίζει τον τύπο, δημιουργεί PDF
με PDFKit, το ανεβάζει στο MinIO και εμφανίζει debug output. Τα έγκυρα messages
γίνονται acknowledged, ενώ τα μη έγκυρα γίνονται rejected.

Στο Kubernetes υπάρχουν init containers ώστε το Node-RED να περιμένει πρώτα
RabbitMQ και MinIO.

## MinIO και PDF αναφορές

Τα PDF οργανώνονται ανά ημερομηνία:

```text
library-audit/
└── loan-reports/
    └── YYYY/MM/DD/
        └── timestamp-event-book-member.pdf
```

Κάθε PDF περιλαμβάνει τύπο ενέργειας, ημερομηνία, τίτλο, συγγραφέα και όνομα
μέλους. Αποθηκεύεται με `Content-Type: application/pdf` και ανοίγει ή κατεβαίνει
από το MinIO Console. Τα IDs δεν εμφανίζονται, αλλά το όνομα μέλους παραμένει
προσωπικό δεδομένο και το console πρέπει να προστατεύεται.

## Docker Compose

### Υπηρεσίες και ports

| Service | Εξωτερική διεύθυνση | Εσωτερικό όνομα |
| --- | --- | --- |
| FastAPI | `http://localhost:8000` | `api:8000` |
| Keycloak | `http://localhost:8080` | `keycloak:8080` |
| RabbitMQ AMQP | `localhost:5672` | `rabbitmq:5672` |
| RabbitMQ Console | `http://localhost:15672` | `rabbitmq:15672` |
| Node-RED | `http://localhost:1880` | `node-red:1880` |
| MinIO API | `http://localhost:9000` | `minio:9000` |
| MinIO Console | `http://localhost:9001` | `minio:9001` |

Όλα τα containers ανήκουν στο `lib-system-network`. Μέσα στο δίκτυο
χρησιμοποιούν service names και όχι `localhost`.

### Images και δεδομένα

- `ghcr.io/user101ig/library-cloud-api:1.0.0`: FastAPI, templates και dependencies.
- `ghcr.io/user101ig/library-cloud-keycloak:1.0.0`: realm import και custom theme.
- `ghcr.io/user101ig/library-cloud-node-red:1.0.0`: flow και Node.js dependencies.
- SQLite: bind mount `./data:/app/data`.
- Keycloak, RabbitMQ και MinIO: ξεχωριστά named volumes.

Τα τρία custom images δημοσιεύονται αυτόματα στο GitHub Container Registry
από το workflow `.github/workflows/publish-images.yml`. Το workflow εκτελείται
σε κάθε push στο `main` και χτίζει εκδόσεις για `linux/amd64` και `linux/arm64`.

Έλεγχος των δημοσιευμένων images:

```bash
docker pull ghcr.io/user101ig/library-cloud-api:1.0.0
docker pull ghcr.io/user101ig/library-cloud-keycloak:1.0.0
docker pull ghcr.io/user101ig/library-cloud-node-red:1.0.0
```

Το `docker compose down` διατηρεί τα δεδομένα. Το `docker compose down -v`
διαγράφει οριστικά τα named volumes, αλλά όχι το bind-mounted `data/library.db`.

### Health checks

- RabbitMQ: `rabbitmq-diagnostics ping`.
- MinIO: `/minio/health/live`.
- FastAPI: `/health`.
- Node-RED ξεκινά αφού RabbitMQ και MinIO είναι healthy.
- FastAPI ξεκινά αφού RabbitMQ είναι healthy και Keycloak έχει ξεκινήσει.

## Αναλυτική τοπική εγκατάσταση

### Προαπαιτούμενα

1. macOS, Linux ή Windows με virtualization.
2. Docker Desktop ή Docker Engine με Compose plugin.
3. Τουλάχιστον 4 GB διαθέσιμη RAM.
4. Ελεύθερες θύρες `8000`, `8080`, `1880`, `5672`, `9000`, `9001`, `15672`.
5. Terminal μέσα στον φάκελο του project.

Το `uv` και η τοπική Python δεν απαιτούνται για το πλήρες Docker setup.

### 1. Μετάβαση στον φάκελο

```bash
cd "/path/to/iro-ergasia"
```

### 2. Environment file

```bash
cp .env.example .env
```

Το `.env.example` περιέχει development defaults. Το `.env` αγνοείται από το
Git και επιτρέπει αλλαγές χωρίς επεξεργασία του Compose.

### 3. Build και εκκίνηση

```bash
docker compose up -d --build
```

Η πρώτη εκτέλεση διαρκεί περισσότερο επειδή κατεβάζει images και dependencies.

### 4. Έλεγχος containers

```bash
docker compose ps
```

Αναμένονται τα services `api`, `keycloak`, `rabbitmq`, `node-red` και `minio`.
Όσα έχουν health check πρέπει να εμφανίζονται ως `healthy`.

### 5. Έλεγχος API

```bash
curl http://localhost:8000/health
```

Αναμενόμενη απάντηση:

```json
{"status":"ok"}
```

### 6. Χρήση εφαρμογής

Άνοιξε `http://localhost:8000`, κάνε login με λογαριασμό από την ενότητα
[Credentials](#credentials) και χρησιμοποίησε το menu ανάλογα με τον ρόλο.
Το OpenAPI documentation βρίσκεται στο `http://localhost:8000/docs`.

### 7. Logs

```bash
docker compose logs --tail=100 api
docker compose logs --tail=100 keycloak
docker compose logs --tail=100 node-red
docker compose logs -f api node-red
```

Το `Ctrl+C` σταματά μόνο την παρακολούθηση των logs.

### 8. Stop και restart

```bash
docker compose stop
docker compose start
docker compose down
```

Πλήρης διαγραφή named volumes:

```bash
docker compose down -v
```

Η τελευταία εντολή διαγράφει Keycloak, RabbitMQ και MinIO data και πρέπει να
χρησιμοποιείται μόνο όταν απαιτείται καθαρό reset.

## Τοπική ανάπτυξη με uv

Για ανάπτυξη, το FastAPI μπορεί να τρέχει εκτός Docker με automatic reload και
οι υπόλοιπες υπηρεσίες μέσα σε containers.

### Προαπαιτούμενα

- Python 3.12 ή νεότερη.
- `uv`.
- Docker για τις υποδομές.

```bash
uv sync
docker compose up -d keycloak rabbitmq minio node-red
docker compose stop api
uv run uvicorn app.main:app --reload
```

Οι local defaults δείχνουν σε `localhost:8080`, `localhost:5672` και
`data/library.db`. Το API δεν μπορεί να τρέχει μέσα και έξω από Docker στην
ίδια θύρα ταυτόχρονα.

## Kubernetes

Τα manifests δημιουργούν namespace, ConfigMap, Secret, τέσσερα PVCs, πέντε
Deployments, Services, health probes και init containers.

### Προαπαιτούμενα

1. Ενεργό Kubernetes cluster.
2. `kubectl`.
3. Local images διαθέσιμα στο cluster.
4. Storage provisioner για τα PVCs.

Σε Docker Desktop δημιουργείται cluster από την ενότητα Kubernetes. Έλεγχος:

```bash
kubectl get nodes
```

Το node πρέπει να είναι `Ready`.

### Deployment σε MicroK8s VM

```bash
sudo snap install microk8s --classic
sudo usermod -a -G microk8s "$USER"
mkdir -p ~/.kube
chmod 0700 ~/.kube
```

Μετά από νέο login στο VM:

```bash
microk8s status --wait-ready
microk8s enable dns hostpath-storage
git clone https://github.com/user101ig/library-cloud.git
cd library-cloud
microk8s kubectl apply -f k8s/
microk8s kubectl get pods -n library-cloud -w
```

Τα manifests χρησιμοποιούν versioned public GHCR images με
`imagePullPolicy: IfNotPresent`. Το VM δεν χρειάζεται να χτίσει images ούτε να
κάνει login στο GitHub Container Registry.

### Έλεγχος και logs

```bash
kubectl get all,pvc -n library-cloud
kubectl logs -n library-cloud deployment/api
kubectl logs -n library-cloud deployment/node-red
```

### Αφαίρεση

```bash
kubectl delete -f k8s/
```

Η διαγραφή περιλαμβάνει τα PVCs και τα δεδομένα του Kubernetes deployment. Τα
Docker Compose volumes είναι ανεξάρτητα.

## Σενάριο παρουσίασης

1. `docker compose up -d --build` και έλεγχος με `docker compose ps`.
2. Login ως `test-librarian`.
3. Δημιουργία βιβλίου και μέλους.
4. Δανεισμός και επιβεβαίωση της διαθεσιμότητας.
5. Έλεγχος exchange και queue στο RabbitMQ Console.
6. Έλεγχος του event στο Node-RED debug panel.
7. Άνοιγμα του PDF στο MinIO Console.
8. Επιστροφή βιβλίου και επιβεβαίωση δεύτερου PDF.
9. Login ως reader για επίδειξη των περιορισμένων δικαιωμάτων.

## Αντιμετώπιση προβλημάτων

### Port already in use

Άλλαξε την αντίστοιχη τιμή στο `.env` ή σταμάτησε το process που χρησιμοποιεί
τη θύρα. Μην τρέχεις Compose και Kubernetes ταυτόχρονα στις ίδιες ports.

### Το Keycloak realm δεν ενημερώθηκε

Το realm εισάγεται κατά την πρώτη δημιουργία του Keycloak volume. Για πλήρες
development reset:

```bash
docker compose down -v
docker compose up -d --build
```

Η εντολή διαγράφει όλα τα named volume data.

### API unhealthy

```bash
docker compose logs api
curl http://localhost:8000/health
```

### RabbitMQ connection error

```bash
docker compose ps rabbitmq
docker compose logs rabbitmq
```

Μέσα στο Docker το API πρέπει να χρησιμοποιεί hostname `rabbitmq`, όχι
`localhost`.

### Δεν δημιουργείται PDF

```bash
docker compose logs node-red
docker compose ps rabbitmq minio node-red
```

Έλεγξε ότι υπάρχει consumer στην queue `library.node-red` και bucket
`library-audit` στο MinIO.

### Kubernetes `ImagePullBackOff`

```bash
docker pull ghcr.io/user101ig/library-cloud-api:1.0.0
```

Επιβεβαίωσε ότι τα GHCR packages είναι public και ότι το image/tag υπάρχει.

### Το `kubectl` δεν βρίσκει cluster

```bash
kubectl config get-contexts
kubectl config use-context docker-desktop
kubectl get nodes
```

## Ασφάλεια και περιορισμοί

Η υλοποίηση είναι εκπαιδευτικό prototype και όχι production deployment.

- Τα demo credentials είναι γνωστά και δεν πρέπει να επαναχρησιμοποιηθούν.
- Η επικοινωνία γίνεται με HTTP αντί HTTPS.
- Τα FastAPI sessions αποθηκεύονται στη μνήμη και χάνονται σε restart.
- Η in-memory αποθήκευση session επιτρέπει μόνο ένα API replica.
- Η SQLite δεν είναι κατάλληλη για distributed writes.
- Τα Kubernetes Secrets περιέχουν development `stringData`.
- Τα management interfaces εκτίθενται μόνο για το demo.
- Τα PDF περιέχουν όνομα μέλους και θεωρούνται προσωπικά δεδομένα.
- RabbitMQ failure δεν κάνει rollback το ολοκληρωμένο loan transaction.

Σε production θα χρησιμοποιούνταν HTTPS, PostgreSQL, Redis session store,
external secret manager, περιορισμένα consoles, backups, monitoring και
retry/dead-letter πολιτική για τα events.

## Κάλυψη τεχνολογιών εργασίας

| Περιοχή | Υλοποίηση |
| --- | --- |
| Identity management | Keycloak, OpenID Connect, roles |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Frontend | Jinja2, HTMX, CSS |
| Messaging | RabbitMQ topic exchange και durable queue |
| Workflow automation | Node-RED |
| Object storage | MinIO και PDF receipts |
| Containers | Dockerfiles και Docker Compose |
| Orchestration | Kubernetes manifests και probes |
| Automated integration | FastAPI → RabbitMQ → Node-RED → MinIO |

Το ThingsBoard δεν χρησιμοποιείται. Το background processing και το audit
archive υλοποιούνται με RabbitMQ, Node-RED και MinIO.
