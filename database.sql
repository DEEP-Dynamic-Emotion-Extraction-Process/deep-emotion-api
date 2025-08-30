CREATE DATABASE deep CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE deep;

-- Tabela de usuários
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY, -- Usando UUID para o ID público
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Nome mais descritivo para a senha
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (email) -- Índice para buscas rápidas por email
);

-- Tabela de vídeos
CREATE TABLE videos (
    id CHAR(36) PRIMARY KEY, -- Usando UUID para o ID público
    user_id CHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    s3_key VARCHAR(255) NOT NULL UNIQUE, -- Campo ESSENCIAL para localizar o arquivo no S3
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING', -- Para controlar o processo assíncrono
    frame_count INT DEFAULT 0, -- O valor real será preenchido após o processamento
    duration_seconds FLOAT DEFAULT 0.0, -- Duração do vídeo, útil para o frontend
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL, -- Para saber quando o processamento terminou

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- Se o usuário for deletado, seus vídeos também serão
);

-- Tabela de frames
CREATE TABLE frames (
    id INT PRIMARY KEY AUTO_INCREMENT, -- ID interno, não precisa ser UUID
    video_id CHAR(36) NOT NULL,
    frame_number INT NOT NULL,
    video_timestamp_sec FLOAT NOT NULL, -- Nome mais claro para o timestamp do vídeo
    emotion ENUM('HAPPY', 'SAD', 'ANGRY', 'SURPRISED', 'NEUTRAL', 'FEAR', 'DISGUST') NOT NULL, -- Mais eficiente e seguro que VARCHAR
    confidence FLOAT NOT NULL,
    
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE, -- Se o vídeo for deletado, seus frames também serão
    UNIQUE KEY (video_id, frame_number) -- Garante que não haja frames duplicados para o mesmo vídeo
);

-- Tabela de logs
CREATE TABLE logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id CHAR(36) NULL, -- NULL para o caso de ações do sistema ou usuário deletado
    action VARCHAR(255) NOT NULL,
    level ENUM('INFO', 'WARN', 'ERROR') NOT NULL DEFAULT 'INFO', -- Nível de severidade do log
    ip_address VARCHAR(45), -- Para auditoria de segurança
    details JSON, -- Campo flexível para armazenar dados extras
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL -- Mantém o log mesmo que o usuário seja deletado
);