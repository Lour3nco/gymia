-- Estrutura do schema gymIA (gerado por exportar_schema.py; não editar à mão)
CREATE SCHEMA IF NOT EXISTS "gymIA";

CREATE TYPE "gymIA".perfil_usuario AS ENUM ('admin', 'instrutor', 'aluno', 'recepcao');
CREATE TYPE "gymIA".status_matricula AS ENUM ('ativa', 'trancada', 'cancelada', 'encerrada');
CREATE TYPE "gymIA".status_pagamento AS ENUM ('pendente', 'pago', 'atrasado', 'cancelado');

CREATE SEQUENCE IF NOT EXISTS "gymIA".alunos_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".alunos_numero_matricula_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".checkins_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".exercicios_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".matriculas_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".pagamentos_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".planos_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".previsoes_evasao_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".sessoes_postura_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".treino_itens_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".treinos_id_seq;
CREATE SEQUENCE IF NOT EXISTS "gymIA".usuarios_id_seq;

CREATE TABLE "gymIA".alunos (
    id bigint DEFAULT nextval('"gymIA".alunos_id_seq'::regclass) NOT NULL,
    usuario_id bigint,
    nome character varying(120) NOT NULL,
    cpf character(11),
    data_nascimento date,
    sexo character(1),
    telefone character varying(20),
    email character varying(150),
    altura_cm numeric(5,2),
    peso_kg numeric(5,2),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    numero_matricula character varying(12) DEFAULT (to_char(now(), 'YYYY'::text) || lpad((nextval('"gymIA".alunos_numero_matricula_seq'::regclass))::text, 6, '0'::text)) NOT NULL,
    CONSTRAINT alunos_cpf_key UNIQUE (cpf),
    CONSTRAINT alunos_numero_matricula_key UNIQUE (numero_matricula),
    CONSTRAINT alunos_usuario_id_key UNIQUE (usuario_id),
    CONSTRAINT alunos_pkey PRIMARY KEY (id),
    CONSTRAINT alunos_sexo_check CHECK ((sexo = ANY (ARRAY['M'::bpchar, 'F'::bpchar, 'O'::bpchar])))
);

CREATE TABLE "gymIA".checkins (
    id bigint DEFAULT nextval('"gymIA".checkins_id_seq'::regclass) NOT NULL,
    aluno_id bigint NOT NULL,
    data_hora timestamp with time zone DEFAULT now() NOT NULL,
    data_saida timestamp with time zone,
    CONSTRAINT checkins_pkey PRIMARY KEY (id)
);

CREATE TABLE "gymIA".exercicios (
    id bigint DEFAULT nextval('"gymIA".exercicios_id_seq'::regclass) NOT NULL,
    nome character varying(120) NOT NULL,
    grupo_muscular character varying(60),
    descricao text,
    CONSTRAINT exercicios_nome_key UNIQUE (nome),
    CONSTRAINT exercicios_pkey PRIMARY KEY (id)
);

CREATE TABLE "gymIA".matriculas (
    id bigint DEFAULT nextval('"gymIA".matriculas_id_seq'::regclass) NOT NULL,
    aluno_id bigint NOT NULL,
    plano_id bigint NOT NULL,
    data_inicio date NOT NULL,
    data_fim date,
    status "gymIA".status_matricula DEFAULT 'ativa'::"gymIA".status_matricula NOT NULL,
    CONSTRAINT matriculas_pkey PRIMARY KEY (id),
    CONSTRAINT matriculas_check CHECK (((data_fim IS NULL) OR (data_fim >= data_inicio)))
);

CREATE TABLE "gymIA".pagamentos (
    id bigint DEFAULT nextval('"gymIA".pagamentos_id_seq'::regclass) NOT NULL,
    matricula_id bigint NOT NULL,
    valor numeric(10,2) NOT NULL,
    data_vencimento date NOT NULL,
    data_pagamento date,
    status "gymIA".status_pagamento DEFAULT 'pendente'::"gymIA".status_pagamento NOT NULL,
    forma_pagamento character varying(30),
    CONSTRAINT pagamentos_pkey PRIMARY KEY (id),
    CONSTRAINT pagamentos_valor_check CHECK ((valor >= (0)::numeric))
);

CREATE TABLE "gymIA".planos (
    id bigint DEFAULT nextval('"gymIA".planos_id_seq'::regclass) NOT NULL,
    nome character varying(80) NOT NULL,
    valor numeric(10,2) NOT NULL,
    duracao_dias integer NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    CONSTRAINT planos_nome_key UNIQUE (nome),
    CONSTRAINT planos_pkey PRIMARY KEY (id),
    CONSTRAINT planos_duracao_dias_check CHECK ((duracao_dias > 0)),
    CONSTRAINT planos_valor_check CHECK ((valor >= (0)::numeric))
);

CREATE TABLE "gymIA".previsoes_evasao (
    id bigint DEFAULT nextval('"gymIA".previsoes_evasao_id_seq'::regclass) NOT NULL,
    aluno_id bigint NOT NULL,
    data_previsao date NOT NULL,
    probabilidade numeric(5,4) NOT NULL,
    modelo_versao character varying(40),
    CONSTRAINT previsoes_evasao_aluno_id_data_previsao_key UNIQUE (aluno_id, data_previsao),
    CONSTRAINT previsoes_evasao_pkey PRIMARY KEY (id),
    CONSTRAINT previsoes_evasao_probabilidade_check CHECK (((probabilidade >= (0)::numeric) AND (probabilidade <= (1)::numeric)))
);

CREATE TABLE "gymIA".sessoes_postura (
    id bigint DEFAULT nextval('"gymIA".sessoes_postura_id_seq'::regclass) NOT NULL,
    aluno_id bigint NOT NULL,
    exercicio_id bigint,
    video_nome character varying(255),
    fps_original numeric(6,2),
    fps_processado numeric(6,2),
    duracao_seg numeric(8,2),
    resultado jsonb,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT sessoes_postura_pkey PRIMARY KEY (id)
);

CREATE TABLE "gymIA".treino_itens (
    id bigint DEFAULT nextval('"gymIA".treino_itens_id_seq'::regclass) NOT NULL,
    treino_id bigint NOT NULL,
    exercicio_id bigint NOT NULL,
    ordem smallint DEFAULT 1 NOT NULL,
    series smallint NOT NULL,
    repeticoes smallint NOT NULL,
    carga_kg numeric(6,2),
    descanso_seg smallint,
    CONSTRAINT treino_itens_pkey PRIMARY KEY (id),
    CONSTRAINT treino_itens_repeticoes_check CHECK ((repeticoes > 0)),
    CONSTRAINT treino_itens_series_check CHECK ((series > 0))
);

CREATE TABLE "gymIA".treinos (
    id bigint DEFAULT nextval('"gymIA".treinos_id_seq'::regclass) NOT NULL,
    aluno_id bigint NOT NULL,
    instrutor_id bigint,
    nome character varying(80) NOT NULL,
    objetivo character varying(120),
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    CONSTRAINT treinos_pkey PRIMARY KEY (id)
);

CREATE TABLE "gymIA".usuarios (
    id bigint DEFAULT nextval('"gymIA".usuarios_id_seq'::regclass) NOT NULL,
    nome character varying(120) NOT NULL,
    email character varying(150) NOT NULL,
    senha_hash character varying(255) NOT NULL,
    perfil "gymIA".perfil_usuario DEFAULT 'aluno'::"gymIA".perfil_usuario NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    criado_em timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT usuarios_email_key UNIQUE (email),
    CONSTRAINT usuarios_pkey PRIMARY KEY (id)
);

ALTER TABLE "gymIA".alunos ADD CONSTRAINT alunos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES "gymIA".usuarios(id) ON DELETE SET NULL;
ALTER TABLE "gymIA".checkins ADD CONSTRAINT checkins_aluno_id_fkey FOREIGN KEY (aluno_id) REFERENCES "gymIA".alunos(id) ON DELETE CASCADE;
ALTER TABLE "gymIA".matriculas ADD CONSTRAINT matriculas_aluno_id_fkey FOREIGN KEY (aluno_id) REFERENCES "gymIA".alunos(id) ON DELETE CASCADE;
ALTER TABLE "gymIA".matriculas ADD CONSTRAINT matriculas_plano_id_fkey FOREIGN KEY (plano_id) REFERENCES "gymIA".planos(id);
ALTER TABLE "gymIA".pagamentos ADD CONSTRAINT pagamentos_matricula_id_fkey FOREIGN KEY (matricula_id) REFERENCES "gymIA".matriculas(id) ON DELETE CASCADE;
ALTER TABLE "gymIA".previsoes_evasao ADD CONSTRAINT previsoes_evasao_aluno_id_fkey FOREIGN KEY (aluno_id) REFERENCES "gymIA".alunos(id) ON DELETE CASCADE;
ALTER TABLE "gymIA".sessoes_postura ADD CONSTRAINT sessoes_postura_aluno_id_fkey FOREIGN KEY (aluno_id) REFERENCES "gymIA".alunos(id) ON DELETE CASCADE;
ALTER TABLE "gymIA".sessoes_postura ADD CONSTRAINT sessoes_postura_exercicio_id_fkey FOREIGN KEY (exercicio_id) REFERENCES "gymIA".exercicios(id);
ALTER TABLE "gymIA".treino_itens ADD CONSTRAINT treino_itens_exercicio_id_fkey FOREIGN KEY (exercicio_id) REFERENCES "gymIA".exercicios(id);
ALTER TABLE "gymIA".treino_itens ADD CONSTRAINT treino_itens_treino_id_fkey FOREIGN KEY (treino_id) REFERENCES "gymIA".treinos(id) ON DELETE CASCADE;
ALTER TABLE "gymIA".treinos ADD CONSTRAINT treinos_aluno_id_fkey FOREIGN KEY (aluno_id) REFERENCES "gymIA".alunos(id) ON DELETE CASCADE;
ALTER TABLE "gymIA".treinos ADD CONSTRAINT treinos_instrutor_id_fkey FOREIGN KEY (instrutor_id) REFERENCES "gymIA".usuarios(id) ON DELETE SET NULL;
