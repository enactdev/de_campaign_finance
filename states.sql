-- phpMyAdmin SQL Dump
-- version 4.6.1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Oct 12, 2016 at 10:09 PM
-- Server version: 5.7.15-0ubuntu0.16.04.1
-- PHP Version: 7.0.8-0ubuntu0.16.04.3

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `de_scrape`
--

--
-- Dumping data for table `states`
--

INSERT INTO `states` (`id`, `abbreviation`, `abbr_lower`, `state`, `has_senate_race`, `num_districts`, `primary_date`, `runoff_date`) VALUES
(1, 'AL', 'al', 'Alabama', 1, 7, '2014-06-03', '2014-07-15'),
(2, 'AK', 'ak', 'Alaska', 1, 1, '2014-08-19', '0000-00-00'),
(3, 'AZ', 'az', 'Arizona', 0, 9, '2014-08-26', '0000-00-00'),
(4, 'AR', 'ar', 'Arkansas', 1, 4, '2014-05-20', '2014-06-10'),
(5, 'CA', 'ca', 'California', 0, 53, '2014-06-03', '0000-00-00'),
(6, 'CO', 'co', 'Colorado', 1, 7, '2014-06-24', '0000-00-00'),
(7, 'CT', 'ct', 'Connecticut', 0, 5, '2014-08-12', '0000-00-00'),
(8, 'DE', 'de', 'Delaware', 1, 1, '2014-09-09', '0000-00-00'),
(9, 'FL', 'fl', 'Florida', 0, 27, '2014-08-26', '0000-00-00'),
(10, 'GA', 'ga', 'Georgia', 1, 14, '2014-05-20', '2014-07-22'),
(11, 'HI', 'hi', 'Hawaii', 1, 2, '2014-08-09', '0000-00-00'),
(12, 'ID', 'id', 'Idaho', 1, 2, '2014-05-20', '0000-00-00'),
(13, 'IL', 'il', 'Illinois', 1, 18, '2014-03-18', '0000-00-00'),
(14, 'IN', 'in', 'Indiana', 0, 9, '2014-05-06', '0000-00-00'),
(15, 'IA', 'ia', 'Iowa', 1, 4, '2014-06-03', '0000-00-00'),
(16, 'KS', 'ks', 'Kansas', 1, 4, '2014-08-05', '0000-00-00'),
(17, 'KY', 'ky', 'Kentucky', 1, 6, '2014-05-20', '0000-00-00'),
(18, 'LA', 'la', 'Louisiana', 0, 6, '0000-00-00', '0000-00-00'),
(19, 'ME', 'me', 'Maine', 1, 2, '2014-06-10', '0000-00-00'),
(20, 'MD', 'md', 'Maryland', 0, 8, '2014-06-24', '0000-00-00'),
(21, 'MA', 'ma', 'Massachusetts', 1, 9, '2014-09-09', '0000-00-00'),
(22, 'MI', 'mi', 'Michigan', 1, 14, '2014-08-05', '0000-00-00'),
(23, 'MN', 'mn', 'Minnesota', 1, 8, '2014-08-12', '0000-00-00'),
(24, 'MS', 'ms', 'Mississippi', 1, 4, '2014-06-03', '2014-06-24'),
(25, 'MO', 'mo', 'Missouri', 0, 8, '2014-08-05', '0000-00-00'),
(26, 'MT', 'mt', 'Montana', 1, 1, '2014-06-03', '0000-00-00'),
(27, 'NE', 'ne', 'Nebraska', 1, 3, '2014-05-13', '0000-00-00'),
(28, 'NV', 'nv', 'Nevada', 0, 4, '2014-06-10', '0000-00-00'),
(29, 'NH', 'nh', 'New Hampshire', 1, 2, '2014-09-09', '0000-00-00'),
(30, 'NJ', 'nj', 'New Jersey', 1, 12, '2014-06-03', '0000-00-00'),
(31, 'NM', 'nm', 'New Mexico', 1, 3, '2014-06-03', '0000-00-00'),
(32, 'NY', 'ny', 'New York', 0, 27, '2014-06-24', '0000-00-00'),
(33, 'NC', 'nc', 'North Carolina', 1, 13, '2014-05-06', '2014-07-15'),
(34, 'ND', 'nd', 'North Dakota', 0, 1, '2014-06-10', '0000-00-00'),
(35, 'OH', 'oh', 'Ohio', 0, 16, '2014-05-06', '0000-00-00'),
(36, 'OK', 'ok', 'Oklahoma', 1, 5, '2014-06-24', '2014-08-26'),
(37, 'OR', 'or', 'Oregon', 1, 5, '2014-05-20', '0000-00-00'),
(38, 'PA', 'pa', 'Pennsylvania', 0, 18, '2014-05-20', '0000-00-00'),
(39, 'RI', 'ri', 'Rhode Island', 1, 2, '2014-09-09', '0000-00-00'),
(40, 'SC', 'sc', 'South Carolina', 1, 7, '2014-06-10', '2014-06-24'),
(41, 'SD', 'sd', 'South Dakota', 1, 1, '2014-06-03', '2014-08-12'),
(42, 'TN', 'tn', 'Tennessee', 1, 9, '2014-08-07', '0000-00-00'),
(43, 'TX', 'tx', 'Texas', 1, 36, '2014-03-04', '2014-05-27'),
(44, 'UT', 'ut', 'Utah', 0, 4, '2014-06-24', '0000-00-00'),
(45, 'VT', 'vt', 'Vermont', 0, 1, '2014-08-26', '0000-00-00'),
(46, 'VA', 'va', 'Virginia', 1, 11, '2014-06-10', '0000-00-00'),
(47, 'WA', 'wa', 'Washington', 0, 10, '2014-08-05', '0000-00-00'),
(48, 'WV', 'wv', 'West Virginia', 1, 3, '2014-05-13', '0000-00-00'),
(49, 'WI', 'wi', 'Wisconsin', 0, 8, '2014-08-12', '0000-00-00'),
(50, 'WY', 'wy', 'Wyoming', 1, 1, '2014-08-19', '0000-00-00'),
(51, 'DC', 'dc', 'District of Columbia', 0, 1, '2014-04-01', '0000-00-00');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
