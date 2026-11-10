# MS3 — Questões legais pendentes

## Para orientadores / equipa

1. Qual é a entidade que irá oferecer e controlar o ApontaUA em operação (UA, DETI, outra unidade, equipa estudantil ou entidade separada)?
2. O acesso a materiais será concedido automaticamente a toda a comunidade autenticada UA ou limitado por seleção humana a cursos/grupos finitos? Qual o universo máximo previsto?
3. A pesquisa e consulta permitem que qualquer membro elegível descubra os materiais de qualquer curso, ou cada autor/representante seleciona destinatários?
4. O conjunto de requisitos de denúncia deve distinguir denúncia de violação de regras da plataforma e aviso de conteúdo alegadamente ilegal? Quem recebe, analisa e responde?
5. As decisões de ocultação/remoção serão comunicadas ao autor com fundamentos e possibilidade de revisão/recurso? Quem decide e em que prazo?
6. Que licença o autor concede à plataforma para armazenar, gerar pré-visualização, mostrar e permitir download do material? A licença é limitada à comunidade UA? O autor pode escolher licença aberta?
7. Que prova de autoria/direitos será pedida para ficheiros, apresentações, exames, soluções ou materiais de terceiros? Como serão tratadas as importações eLearning?
8. Quem aprova os Termos e Condições e a política específica do serviço antes do piloto?
9. Está aprovado o uso dos dados/atributos do IdP e quais são os atributos permitidos, a base institucional e os acordos operacionais?
10. Que política STIC rege uso aceitável, alojamento, segurança, incidentes, backups e logs para aplicações construídas por estudantes?
11. Qual componente de proxy é a decisão atual? O contexto recebido indica Apache, mas o NFR v2.0 define NGINX (NFR-53/NFR-60) e a arquitetura v2.0 consultada também aponta NGINX.

## Para sTIC / IT

1. Autoriza-se formalmente o alojamento do ApontaUA no host referido e em que condições técnicas, de segurança, rede, DNS, backups e disponibilidade?
2. Qual sistema IdP/WSO2, protocolo, client registration, claims, scopes, sessão/logout e restrições de uso são autorizados?
3. Quem é o responsável operacional e ponto de contacto para segurança e incidentes?
4. A UA disponibiliza uma política atual de segurança e utilização aceitável aplicável à plataforma?

## Para EPD / serviços jurídicos UA

1. A UA será responsável pelo tratamento, responsável conjunto ou apenas fornecedora de identidade/infraestrutura? Quem aprova o tratamento e aviso aos titulares?
2. É necessária AIPD, consulta prévia ou outra análise institucional antes do piloto?
3. Qual fundamento de licitude, retenção e processo de direitos dos titulares se aplica a contas, reputação, denúncias, logs e materiais?
4. Que procedimentos de direitos de autor e remoção devem aplicar-se a materiais estudantis e conteúdos retirados do eLearning?
5. A qualificação da entidade/serviço e modelo de acesso coloca o ApontaUA no âmbito do DSA como serviço de alojamento ou plataforma em linha? Que obrigações e exceções concretas resultam?
6. Sendo a UA uma entidade pública, que obrigações de acessibilidade, declaração e selo se aplicam ao domínio/app e à entidade responsável?

## Para responsável técnico

1. A equipa confirma npm + `package-lock.json` para o frontend e uv + `uv.lock` para o backend como processo de instalação e atualização reprodutível?
2. O `Dockerfile` e o README do backend usam uv para consumir `uv.lock`. A equipa confirma esta escolha de ferramenta e a versão uv 0.13.7 para o processo de build?
3. Qual a política para licenciar o próprio código ApontaUA e distribuir notices/SBOM nas imagens e releases?

Não foram presumidas respostas a estas perguntas.
