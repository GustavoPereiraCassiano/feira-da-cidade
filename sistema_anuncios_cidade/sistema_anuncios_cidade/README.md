# Sistema de Anúncios da Cidade

Aplicação web baseada no Documento de Software (Entrega 1), usando Flask, SQLite, SQLAlchemy, Bootstrap, Flask-SocketIO, Pillow, APScheduler e ReportLab.

## 1. Requisitos

- Python 3.10 ou superior
- pip
- Navegador atualizado

## 2. Instalação no Windows (PowerShell)

```powershell
# Entre na pasta do projeto
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

# Crie o arquivo de configuração
Copy-Item .env.example .env
```

Edite o `.env` e altere, no mínimo, `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` e `WHATSAPP_NUMBER`.

## 3. Executar

```powershell
python run.py
```

Abra http://127.0.0.1:5000

## 4. Primeiro acesso administrativo

O administrador é criado automaticamente na primeira inicialização, usando `ADMIN_EMAIL` e `ADMIN_PASSWORD` do `.env`. Entre em `/conta/login` com essas credenciais.

**Importante:** troque a senha padrão antes de disponibilizar o sistema. Não publique o arquivo `.env`.

## 5. Funcionalidades implementadas

- Cadastro, login, logout e edição de perfil de vendedores.
- Senhas armazenadas com hash do Werkzeug.
- Publicação de anúncios com título, descrição, preço, categoria e pelo menos uma foto.
- Compressão/redimensionamento de imagens com Pillow, buscando limite de 200 KB.
- Vídeo opcional em MP4 ou WEBM.
- Página inicial por categoria, até seis anúncios por categoria, com busca e filtros.
- Detalhes do anúncio e identificação do vendedor.
- Edição, remoção e marcação de anúncio como vendido.
- Registro da venda com comprador opcional.
- Chat em tempo real com Flask-SocketIO e histórico persistido no banco.
- Caixa de entrada de conversas do vendedor.
- Painel administrativo e moderação de anúncios.
- Relatório PDF mensal e agendamento para o dia 1º às 07:00.
- Atalho de suporte pelo WhatsApp.
- Testes iniciais com pytest.

## 6. Testes

```powershell
pytest -q
```

## 7. Estrutura

```text
sistema_anuncios_cidade/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes.py
│   ├── utils.py
│   ├── reports.py
│   ├── scheduler.py
│   ├── templates/
│   └── static/
├── tests/
├── instance/              # banco, uploads e relatórios locais
├── .env.example
├── requirements.txt
└── run.py
```

## 8. Observações importantes antes de produção

Este pacote é uma primeira implementação funcional do MVP para execução local e avaliação. Antes de publicar na internet, recomenda-se:
- configurar HTTPS e uma `SECRET_KEY` forte;
- trocar SQLite por PostgreSQL se houver múltiplos processos/maior volume;
- configurar armazenamento persistente e backup das mídias;
- restringir e validar ainda mais o acesso às salas do chat (incluindo tokens de sessão do comprador);
- configurar um servidor Socket.IO compatível com produção;
- adicionar paginação, limitação de tentativas de login e política de privacidade/termos;
- validar os arquivos de vídeo por conteúdo e tamanho;
- ajustar o relatório para o período mensal desejado (o agendamento atual gera o mês corrente no dia 1º; pode ser adaptado para o mês anterior conforme a regra final do professor/cliente).

O nome “Feira da Cidade” e a marca “FC” são provisórios e podem ser substituídos pela identidade visual definitiva.
