""" basic tests """

import logging
import fail2ban_importer

def test_setup_logging() -> None:
    """ this is a gimmie """

    logger = fail2ban_importer.setup_logging("INFO")
    assert logger.level == logging.INFO


    logger = fail2ban_importer.setup_logging("debug")
    assert logger.level == logging.DEBUG

    logger = fail2ban_importer.setup_logging("CHEESE")
    assert logger.level == logging.DEBUG
