-- Drop existing tables if needed
DROP TABLE IF EXISTS templates;
DROP TABLE IF EXISTS pages;

-- Create the pages table
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base64_image TEXT NOT NULL,
    name TEXT,
    agent_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the templates table
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base64_image TEXT NOT NULL,
    caption TEXT NOT NULL,
    page_name TEXT,
    agent_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_name) REFERENCES pages(name) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pages_agent_name 
ON pages(agent_name);

CREATE INDEX IF NOT EXISTS idx_templates_agent_name 
ON templates(agent_name);

-- Create trigger for pages
CREATE TRIGGER IF NOT EXISTS update_pages_updated_at
AFTER UPDATE ON pages
FOR EACH ROW
BEGIN
    UPDATE pages SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Create trigger for templates
CREATE TRIGGER IF NOT EXISTS update_templates_updated_at
AFTER UPDATE ON templates
FOR EACH ROW
BEGIN
    UPDATE templates SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;