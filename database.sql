CREATE DATABASE deep CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE deep;

CREATE TABLE users (
    id CHAR(36) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (email) 
);

CREATE TABLE videos (
    id CHAR(36) PRIMARY KEY, 
    user_id CHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    s3_key VARCHAR(255) NOT NULL UNIQUE,
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING', 
    frame_count INT DEFAULT 0,
    duration_seconds FLOAT DEFAULT 0.0, 
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE frames (
    id INT PRIMARY KEY AUTO_INCREMENT,
    video_id CHAR(36) NOT NULL,
        frame_number INT NOT NULL,
        video_timestamp_sec FLOAT NOT NULL, 
    emotion ENUM('HAPPY', 'SAD', 'ANGRY', 'SURPRISED', 'NEUTRAL', 'FEAR', 'DISGUST', 'UNIDENTIFIED') NOT NULL,
    confidence FLOAT NOT NULL,
    
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
    UNIQUE KEY (video_id, frame_number) 
);

CREATE TABLE logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id CHAR(36) NULL, 
    action VARCHAR(255) NOT NULL,
    level ENUM('INFO', 'WARN', 'ERROR') NOT NULL DEFAULT 'INFO',
    ip_address VARCHAR(45),
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);