DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `GetUpdatedIssues`(
    IN start_date DATETIME,
    IN end_date DATETIME
)
BEGIN
    SELECT id
    FROM mantis_bug_table
    WHERE FROM_UNIXTIME(last_updated) BETWEEN start_date AND end_date;
END$$
DELIMITER ;
