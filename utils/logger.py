import logging

def get_user_logger(user_id: int) -> logging.Logger:
    """Возвращает логгер, который пишет в файл {user_id}.log"""
    logger_name = f"user_{user_id}"
    logger = logging.getLogger(logger_name)
    
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    log_filename = f"{user_id}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger