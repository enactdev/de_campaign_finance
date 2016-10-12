
UPDATE `candidate` SET `slug` = 
    LOWER( TRIM( TRAILING '-' FROM REPLACE( REPLACE( REPLACE( 
        CONCAT( name_first, '-', name_middle, '-', name_last, '-', name_suffix ) 
      ,'.', ''), '--', '-'), '--', '-')));


