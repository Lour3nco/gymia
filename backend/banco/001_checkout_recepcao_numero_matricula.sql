-- Alterações feitas no banco em out/2026 (já aplicadas no Supabase). Pode rodar de novo: é idempotente.

-- 1) Check-out: hora de saída do check-in (vazia enquanto o aluno está na academia)
ALTER TABLE "gymIA".checkins ADD COLUMN IF NOT EXISTS data_saida timestamp NULL;

-- 2) Perfil de recepção (o enum só tinha admin, instrutor e aluno)
ALTER TYPE "gymIA".perfil_usuario ADD VALUE IF NOT EXISTS 'recepcao';

-- 3) Número de matrícula: ano + sequência de 6 dígitos (ex.: 2026000001), gerado pelo banco em todo cadastro
CREATE SEQUENCE IF NOT EXISTS "gymIA".alunos_numero_matricula_seq;
ALTER TABLE "gymIA".alunos ADD COLUMN IF NOT EXISTS numero_matricula varchar(12)
    DEFAULT (to_char(now(), 'YYYY') || lpad(nextval('"gymIA".alunos_numero_matricula_seq')::text, 6, '0'));
UPDATE "gymIA".alunos SET numero_matricula = to_char(criado_em, 'YYYY')
    || lpad(nextval('"gymIA".alunos_numero_matricula_seq')::text, 6, '0')
    WHERE numero_matricula IS NULL;
ALTER TABLE "gymIA".alunos ALTER COLUMN numero_matricula SET NOT NULL;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'alunos_numero_matricula_key') THEN
        ALTER TABLE "gymIA".alunos ADD CONSTRAINT alunos_numero_matricula_key UNIQUE (numero_matricula);
    END IF;
END $$;
