# MatVerse Container Environment
## Relatório do Ambiente de Desenvolvimento — QIG-Σ

> **Projeto:** MatVerse / QIG-Σ
> **Imagem base:** `ubuntu:22.04` (LTS)
> **Propósito:** Ambiente de desenvolvimento reproduzível para a stack completa MatVerse
> **Data de geração:** 2026-02-20
> **Mantenedor:** xMatVerse

---

## 1. Visão Geral

O container MatVerse fornece um ambiente de desenvolvimento isolado e reproduzível que agrega as ferramentas fundamentais utilizadas no ecossistema QIG-Σ. A imagem é construída a partir do Ubuntu 22.04 LTS e inclui linguagens de programação, runtimes e utilitários necessários para o desenvolvimento, teste e depuração de aplicações MatVerse.

O objetivo principal é garantir paridade entre ambientes de desenvolvimento locais, CI/CD e produção, eliminando problemas de compatibilidade entre versões de ferramentas.

---

## 2. Componentes Instalados

| Ferramenta            | Versão      | Método de Instalação         | Finalidade                          |
|-----------------------|-------------|-------------------------------|-------------------------------------|
| **Ubuntu**            | 22.04 LTS   | Imagem base (`ubuntu:22.04`)  | Sistema operacional base            |
| **Google Chrome**     | Unstable     | APT (repositório Google)      | Testes E2E, automação web           |
| **Node.js**           | 20.19.6      | NodeSource (`setup_20.x`)     | Runtime JavaScript / servidor       |
| **npm**               | latest       | Bundled com Node.js           | Gerenciador de pacotes Node         |
| **Yarn**              | 4.12.0       | Corepack (`corepack prepare`) | Gerenciador de pacotes alternativo  |
| **Python**            | 3.12         | deadsnakes PPA                | Scripts, tooling, ML pipelines      |
| **pip**               | system       | Bundled com Python            | Gerenciador de pacotes Python       |
| **Go**                | 1.24.3       | Binário oficial (go.dev/dl)   | Backend / microserviços             |
| **Rust**              | 1.89.0       | rustup                        | Componentes de performance          |
| **Cargo**             | 1.89.0       | Bundled com Rust (rustup)     | Gerenciador de pacotes Rust         |
| **rustfmt**           | stable       | rustup component              | Formatador de código Rust           |
| **clippy**            | stable       | rustup component              | Linter para Rust                    |

---

## 3. Sequência de Inicialização do Ambiente

A seguir, a sequência de operações executadas durante o build da imagem:

```
[BOOT] Iniciando build da imagem MatVerse...
[INFO] Base: ubuntu:22.04

[STEP 1/8] Atualizando repositórios APT e instalando pacotes base
  + apt-get update
  + Instalando: curl, wget, git, gnupg, build-essential, ca-certificates,
                libssl-dev, pkg-config, software-properties-common ...
  ✓ Pacotes base instalados com sucesso

[STEP 2/8] Instalando Google Chrome Unstable
  + Adicionando chave GPG: dl.google.com/linux/linux_signing_key.pub
  + Adicionando repositório: https://dl.google.com/linux/chrome/deb/
  + apt-get install google-chrome-unstable
  ✓ Chrome Unstable instalado

[STEP 3/8] Instalando Node.js 20.19.6
  + Executando NodeSource setup_20.x
  + apt-get install nodejs
  + npm install -g npm@latest
  ✓ Node.js 20.19.6 disponível em /usr/bin/node

[STEP 4/8] Configurando Yarn 4.12.0
  + corepack enable
  + corepack prepare yarn@4.12.0 --activate
  ✓ Yarn 4.12.0 ativo via corepack

[STEP 5/8] Instalando Python 3.12
  + Adicionando PPA: ppa:deadsnakes/ppa
  + apt-get install python3.12 python3.12-dev python3.12-venv python3-pip
  + Configurando update-alternatives: python3 → python3.12
  ✓ Python 3.12 disponível em /usr/bin/python3

[STEP 6/8] Instalando Go 1.24.3
  + Download: https://go.dev/dl/go1.24.3.linux-amd64.tar.gz
  + Extraindo para /usr/local/go
  + Criando diretórios: /root/go/{bin,pkg,src}
  ✓ Go 1.24.3 disponível em /usr/local/go/bin/go

[STEP 7/8] Instalando Rust 1.89.0
  + Executando instalador rustup (--default-toolchain 1.89.0)
  + rustup component add clippy rustfmt
  ✓ Rust 1.89.0 disponível em /root/.cargo/bin/rustc

[STEP 8/8] Verificação do ambiente (smoke test)
  $ node --version        → v20.19.6  ✓
  $ yarn --version        → 4.12.0    ✓
  $ python3 --version     → 3.12.x    ✓
  $ go version            → go1.24.3  ✓
  $ rustc --version       → 1.89.0    ✓
  $ google-chrome-unstable → ok       ✓

[BOOT] Ambiente MatVerse inicializado com sucesso. WORKDIR: /workspace
```

---

## 4. Variáveis de Ambiente Configuradas

| Variável        | Valor                     | Descrição                                  |
|-----------------|---------------------------|---------------------------------------------|
| `GOROOT`        | `/usr/local/go`           | Diretório de instalação do Go               |
| `GOPATH`        | `/root/go`                | Workspace Go (bin, pkg, src)                |
| `CARGO_HOME`    | `/root/.cargo`            | Home do Cargo/rustup binaries               |
| `RUSTUP_HOME`   | `/root/.rustup`           | Home do rustup toolchains                   |
| `TZ`            | `America/Sao_Paulo`       | Fuso horário do container                   |
| `DEBIAN_FRONTEND` | `noninteractive`        | Evita prompts interativos no APT            |
| `PATH`          | `/usr/local/go/bin:/root/go/bin:/root/.cargo/bin:...` | PATH atualizado com todas as ferramentas |

---

## 5. Uso do Container

### Build da imagem

```bash
# Construir a imagem localmente
docker build -f Dockerfile.matverse -t matverse:latest .

# Build com tag de versão
docker build -f Dockerfile.matverse -t matverse:1.0.0 .
```

### Execução do container

```bash
# Iniciar container interativo
docker run -it --rm matverse:latest

# Montar o projeto e iniciar sessão de desenvolvimento
docker run -it --rm \
  -v "$(pwd)":/workspace \
  -p 3000:3000 \
  -p 8080:8080 \
  matverse:latest

# Executar um comando específico
docker run --rm matverse:latest node --version
docker run --rm matverse:latest go version
docker run --rm matverse:latest rustc --version
```

### Verificar versões instaladas

```bash
docker run --rm matverse:latest bash -c "
  echo '=== MatVerse Stack Versions ==='
  echo 'Node.js:' \$(node --version)
  echo 'Yarn:   ' \$(yarn --version)
  echo 'Python: ' \$(python3 --version)
  echo 'Go:     ' \$(go version)
  echo 'Rust:   ' \$(rustc --version)
"
```

---

## 6. Estrutura de Diretórios do Container

```
/
├── usr/
│   ├── local/
│   │   └── go/              ← Instalação do Go 1.24.3
│   └── bin/
│       ├── node             ← Node.js 20.19.6
│       ├── python3 → python3.12
│       └── yarn             ← via corepack
├── root/
│   ├── .cargo/              ← Rust/Cargo binários
│   ├── .rustup/             ← rustup toolchains
│   └── go/                  ← GOPATH workspace
│       ├── bin/
│       ├── pkg/
│       └── src/
└── workspace/               ← WORKDIR padrão (monte seu projeto aqui)
```

---

## 7. Notas e Observações

### Chrome Unstable
O canal **Unstable** do Google Chrome é utilizado para garantir acesso às funcionalidades mais recentes do browser durante testes automatizados (Puppeteer, Playwright). Para ambientes de produção onde estabilidade é crítica, substitua por `google-chrome-stable`.

### Rust 1.89.0
A versão 1.89.0 do Rust está fixada via `rustup --default-toolchain`. Para atualizar para uma versão mais recente, reconstrua a imagem alterando o argumento no `Dockerfile.matverse`.

### Política de Atualizações
As versões das ferramentas são **fixadas** intencionalmente para garantir reprodutibilidade. Atualizações devem ser realizadas de forma controlada, alterando as versões no `Dockerfile.matverse` e validando a compatibilidade antes de promover para produção.

### Segurança
Esta imagem é destinada a ambientes de **desenvolvimento**. Para uso em produção:
- Remova ferramentas desnecessárias
- Use um usuário não-root (`USER <user>`)
- Considere uma abordagem multi-stage para reduzir a superfície de ataque

---

*Relatório gerado automaticamente para o projeto MatVerse / QIG-Σ — xMatVerse © 2026*
