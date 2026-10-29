-- Database Initialization & Seeding Script for LANGUAAI
CREATE DATABASE IF NOT EXISTS `language_app`;
USE `language_app`;

-- Clear existing data if re-seeding
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE `quiz`;
TRUNCATE TABLE `lessons`;
TRUNCATE TABLE `languages`;
SET FOREIGN_KEY_CHECKS = 1;

-- Seed 20 Languages
INSERT INTO `languages` (`id`, `name`, `code`) VALUES
(1, 'French', 'fr'), (2, 'Spanish', 'es'), (3, 'German', 'de'), (4, 'Italian', 'it'),
(5, 'Portuguese', 'pt'), (6, 'Japanese', 'ja'), (7, 'Mandarin Chinese', 'zh'), (8, 'Korean', 'ko'),
(9, 'Arabic', 'ar'), (10, 'Russian', 'ru'), (11, 'Hindi', 'hi'), (12, 'Dutch', 'nl'),
(13, 'Turkish', 'tr'), (14, 'Polish', 'pl'), (15, 'Swedish', 'sv'), (16, 'Greek', 'el'),
(17, 'Vietnamese', 'vi'), (18, 'Indonesian', 'id'), (19, 'Swahili', 'sw'), (20, 'Hebrew', 'he');

-- Seed Lessons (Sample for French)
INSERT INTO `lessons` (`language_id`, `title`, `content`) VALUES
(1, 'French Basics & Essential Phrases', '1. Bonjour = Hello / Good Morning\n2. Merci = Thank you\n3. Au revoir = Goodbye\n4. Oui = Yes\n5. Non = No\n6. S\'il vous plaît = Please\n7. Excusez-moi = Excuse me\n8. Comment ça va? = How are you?');

-- Seed Quiz Questions (Sample 50-Question Schema for French - ID 1)
INSERT INTO `quiz` (`language_id`, `question`, `option_a`, `option_b`, `option_c`, `option_d`, `answer`, `explanation`) VALUES
(1, 'What is the English translation of "Bonjour"?', 'Goodbye', 'Hello', 'Thank You', 'Please', 'Hello', '"Bonjour" is the standard French daytime greeting meaning "Hello" or "Good morning".'),
(1, 'What does "Merci" mean in English?', 'Sorry', 'Please', 'Thank you', 'Goodbye', 'Thank you', '"Merci" is used across all French-speaking regions to express gratitude.'),
(1, 'How do you say "Goodbye" in French?', 'Bonjour', 'Au revoir', 'Oui', 'Non', 'Au revoir', '"Au revoir" literally translates to "until we see each other again".'),
(1, 'What is the French word for "Yes"?', 'Non', 'Merci', 'Oui', 'Bonjour', 'Oui', '"Oui" signifies affirmative confirmation in French.'),
(1, 'What is the French word for "No"?', 'Oui', 'Non', 'Pardon', 'S\'il vous plaît', 'Non', '"Non" is the direct standard negation in French.');