# DZOO · Gestão de Aquisições (protótipo v0.2)

Aplicativo Streamlit experimental para gestão das aquisições do Departamento de Zootecnia da UFSJ.

## Novidades da versão 0.2

- Consulta prioritária por **pregão**, preservando os vínculos de cada item com a respectiva ata e fornecedor.
- Importação assistida de **vários PDFs anexados**, **arquivo PDF por link público** ou **pasta pública do Google Drive** (via biblioteca `gdown`).
- Extração preliminar de metadados e tabelas com PyMuPDF. A qualidade depende do formato do PDF; arquivos digitalizados ou tabelas não estruturadas podem requerer cadastro manual.
- Prévia editável dos itens encontrados, com checkbox **Importar para DEZOO**.
- **Somente itens explicitamente selecionados** são persistidos; duplicidades por ata + número do item são ignoradas.
- Mantidos os módulos de planejamento, PPLAN, requisições, empenhos, recebimentos por DANFE e relatórios da versão 0.1.

## Executar localmente

```powershell
pip install -r requirements.txt
python -m streamlit run app.py
```

Na área **Pregões e itens de interesse do DEZOO**, use a aba **Importar e selecionar itens**. Escolha PDFs ou link Drive público, clique em **Ler PDFs** ou **Buscar PDFs do Drive**, depois em **Extrair itens e preparar conferência**. Revise cada linha, marque apenas os itens desejados e confirme o cadastro.

## Publicar no GitHub / Streamlit

1. **Não envie o ZIP inteiro como arquivo**: descompacte-o.
2. Envie os arquivos `app.py`, `importador.py`, `requirements.txt`, `.gitignore` e `README.md` **para a mesma pasta do repositório**.
3. Se mantiver a estrutura antiga do GitHub, substitua o `app.py` e demais arquivos dentro de `dzoo_streamlit_prototipo_v01/dzoo_streamlit/`. O campo `Main file path` continua `dzoo_streamlit_prototipo_v01/dzoo_streamlit/app.py`.
4. Para novo repositório com arquivos na raiz, o campo `Main file path` será `app.py`.
5. O Streamlit normalmente atualiza automaticamente o aplicativo após o commit no GitHub.

## Limitações e segurança

- **Protótipo para avaliação com dados fictícios**: SQLite local não oferece persistência segura no Streamlit Community Cloud e o aplicativo ainda não possui autenticação. Não insira informações administrativas sensíveis em um app público.
- Links públicos podem ser bloqueados por limitação do Google ou por alteração do compartilhamento. Nesse caso, use upload de PDF.
- Os dados extraídos de PDF **não são necessariamente fiéis**: conferir item, quantidade, unidade, fornecedor e preço antes de salvar. Não considera digitalização sem camada de texto (OCR não implementado).
- A data de vigência das atas **não é inferida automaticamente** e deve ser confirmada nos documentos oficiais antes de utilizar o saldo para novas compras.
- As movimentações cadastradas no app **não são consulta oficial ao SIPAC**; o saldo de ata é apenas cálculo interno.
- Não existe integração real com SIPAC, Compras.gov, PNCP nem envio de e-mail.
- O botão de carga fictícia só funciona se o banco estiver vazio.

## Melhorias v0.3

- Na importação: botões **Selecionar todos** e **Desmarcar todos**.
- Seleção separada em uma tabela compacta com caixa de seleção, número do item e nome lado a lado (sem necessidade de rolar horizontalmente para encontrar a caixa). A tabela de conferência detalhada fica abaixo. Apenas itens marcados serão gravados.
- Na área **Pregões**, aba **Excluir item importado**, exclusão mediante confirmação. Itens já vinculados a PPLAN, requisições ou empenhos ficam protegidos.
- Em **Requisições SIPAC**, selecionar um fornecedor e adicionar vários itens dele na mesma requisição, com quantidade individual; uma requisição não pode misturar fornecedores. Uma requisição existente pode receber novos itens do mesmo fornecedor, desde que não sejam repetidos.

**Atualização**: substitua `app.py`, `importador.py`, `requirements.txt` e `README.md` no diretório que o Streamlit utiliza. Os dados locais SQLite existentes não são apagados por esta atualização do código. O aplicativo de demonstração ainda requer banco persistente e autenticação antes do uso administrativo em produção.
