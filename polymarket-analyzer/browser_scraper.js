/**
 * Polymarket Browser Scraper
 * סקריפט לחילוץ נתוני פוזיציות מ-Polymarket באמצעות Puppeteer
 *
 * שימוש: node browser_scraper.js [username]
 * דוגמה: node browser_scraper.js anoin123
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const USERNAME = process.argv[2] || 'anoin123';
const OUTPUT_DIR = path.join(__dirname, 'output');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function scrapePolymarketPositions(username) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`מתחיל חילוץ נתונים עבור: @${username}`);
    console.log(`${'='.repeat(60)}\n`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const page = await browser.newPage();

        // Set viewport
        await page.setViewport({ width: 1920, height: 1080 });

        // Set user agent
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

        const url = `https://polymarket.com/@${username}?tab=positions`;
        console.log(`טוען את הדף: ${url}`);

        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 60000
        });

        // Wait for the positions to load
        console.log('ממתין לטעינת פוזיציות...');
        await page.waitForSelector('[data-testid="position-card"], .c-position-card, [class*="position"]', {
            timeout: 30000
        }).catch(() => {
            console.log('לא נמצאו קומפוננטות פוזיציה ספציפיות, מנסה גישה חלופית...');
        });

        // Scroll to load all positions (infinite scroll)
        console.log('גולל את הדף לטעינת כל הפוזיציות...');
        let previousHeight = 0;
        let scrollAttempts = 0;
        const maxScrollAttempts = 20;

        while (scrollAttempts < maxScrollAttempts) {
            const currentHeight = await page.evaluate(() => document.body.scrollHeight);

            if (currentHeight === previousHeight) {
                break;
            }

            await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
            await new Promise(resolve => setTimeout(resolve, 1500));

            previousHeight = currentHeight;
            scrollAttempts++;
            console.log(`גלילה ${scrollAttempts}/${maxScrollAttempts}...`);
        }

        // Scroll back to top
        await page.evaluate(() => window.scrollTo(0, 0));
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Extract positions data
        console.log('\nמחלץ נתוני פוזיציות...');

        const positions = await page.evaluate(() => {
            const data = [];

            // Try multiple selectors for position cards
            const selectors = [
                '[data-testid="position-card"]',
                '.c-position-card',
                '[class*="position-card"]',
                '[class*="PositionCard"]',
                'article[class*="position"]',
                'div[class*="portfolio"] > div > div'
            ];

            let cards = [];
            for (const selector of selectors) {
                cards = document.querySelectorAll(selector);
                if (cards.length > 0) break;
            }

            // If no specific cards found, try to find position-like elements
            if (cards.length === 0) {
                // Look for elements containing price percentages
                const allElements = document.querySelectorAll('div, article, section');
                cards = Array.from(allElements).filter(el => {
                    const text = el.textContent || '';
                    return (text.includes('$') || text.includes('%')) &&
                           (text.toLowerCase().includes('yes') || text.toLowerCase().includes('no')) &&
                           el.children.length > 2;
                });
            }

            cards.forEach((card, index) => {
                try {
                    const text = card.textContent || '';

                    // Extract market name (usually the longest text block)
                    let marketName = '';
                    const headings = card.querySelectorAll('h1, h2, h3, h4, a[href*="/event/"], [class*="title"], [class*="market"]');
                    if (headings.length > 0) {
                        marketName = headings[0].textContent.trim();
                    }

                    // Extract Yes/No type
                    let posType = 'Unknown';
                    if (text.toLowerCase().includes('yes')) {
                        posType = 'Yes';
                    } else if (text.toLowerCase().includes('no')) {
                        posType = 'No';
                    }

                    // Extract prices (looking for patterns like $0.XX or XX%)
                    const priceMatches = text.match(/\$?(\d+\.?\d*)[%¢]?/g) || [];
                    const percentMatches = text.match(/(\d+\.?\d*)%/g) || [];

                    // Extract dollar amounts
                    const dollarMatches = text.match(/\$(\d+\.?\d*)/g) || [];

                    // Try to find specific labeled values
                    let avgPrice = '';
                    let currentPrice = '';
                    let shares = '';
                    let value = '';
                    let pnl = '';

                    // Look for specific patterns
                    const avgMatch = text.match(/avg[^\d]*(\d+\.?\d*)[¢%]?/i);
                    if (avgMatch) avgPrice = avgMatch[1];

                    const currentMatch = text.match(/current[^\d]*(\d+\.?\d*)[¢%]?/i);
                    if (currentMatch) currentPrice = currentMatch[1];

                    const sharesMatch = text.match(/(\d+\.?\d*)\s*shares/i);
                    if (sharesMatch) shares = sharesMatch[1];

                    const valueMatch = text.match(/value[^\$]*\$(\d+\.?\d*)/i);
                    if (valueMatch) value = valueMatch[1];

                    const pnlMatch = text.match(/([+-]?\$?\d+\.?\d*)\s*\(?([+-]?\d+\.?\d*)%\)?/);
                    if (pnlMatch) pnl = pnlMatch[0];

                    if (marketName || dollarMatches.length > 0) {
                        data.push({
                            index: index + 1,
                            marketName: marketName || `Position ${index + 1}`,
                            type: posType,
                            avgPrice: avgPrice || (percentMatches[0] || ''),
                            currentPrice: currentPrice || (percentMatches[1] || ''),
                            shares: shares,
                            value: value || (dollarMatches[0] || ''),
                            pnl: pnl,
                            rawText: text.substring(0, 500)
                        });
                    }
                } catch (e) {
                    console.error('Error extracting position:', e);
                }
            });

            return data;
        });

        console.log(`נמצאו ${positions.length} פוזיציות`);

        // Try to get user stats
        const userStats = await page.evaluate(() => {
            const stats = {};

            // Look for portfolio value
            const valueMatches = document.body.textContent.match(/Portfolio Value[:\s]*\$?([\d,]+\.?\d*)/i);
            if (valueMatches) stats.portfolioValue = valueMatches[1];

            // Look for total PnL
            const pnlMatches = document.body.textContent.match(/Total P&?L[:\s]*([+-]?\$?[\d,]+\.?\d*)/i);
            if (pnlMatches) stats.totalPnL = pnlMatches[1];

            // Look for number of positions
            const posMatches = document.body.textContent.match(/(\d+)\s*Positions?/i);
            if (posMatches) stats.positionCount = posMatches[1];

            return stats;
        });

        console.log('\nסטטיסטיקות משתמש:');
        console.log(JSON.stringify(userStats, null, 2));

        // Take a screenshot
        const screenshotPath = path.join(OUTPUT_DIR, `screenshot_${username}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(`\nצילום מסך נשמר: ${screenshotPath}`);

        // Get page HTML for debugging
        const htmlContent = await page.content();
        const htmlPath = path.join(OUTPUT_DIR, `page_${username}.html`);
        fs.writeFileSync(htmlPath, htmlContent);
        console.log(`HTML נשמר: ${htmlPath}`);

        // Save positions data
        const jsonPath = path.join(OUTPUT_DIR, `browser_positions_${username}.json`);
        fs.writeFileSync(jsonPath, JSON.stringify({
            username,
            scrapedAt: new Date().toISOString(),
            stats: userStats,
            positions
        }, null, 2));
        console.log(`נתונים נשמרו: ${jsonPath}`);

        return { positions, userStats };

    } catch (error) {
        console.error('שגיאה:', error.message);
        throw error;
    } finally {
        await browser.close();
    }
}

function analyzePositions(positions) {
    console.log(`\n${'='.repeat(60)}`);
    console.log('ניתוח פוזיציות');
    console.log(`${'='.repeat(60)}\n`);

    if (positions.length === 0) {
        console.log('לא נמצאו פוזיציות לניתוח');
        return;
    }

    // Count Yes vs No positions
    const yesCount = positions.filter(p => p.type === 'Yes').length;
    const noCount = positions.filter(p => p.type === 'No').length;

    console.log(`סה"כ פוזיציות: ${positions.length}`);
    console.log(`פוזיציות Yes: ${yesCount} (${(yesCount/positions.length*100).toFixed(1)}%)`);
    console.log(`פוזיציות No: ${noCount} (${(noCount/positions.length*100).toFixed(1)}%)`);

    console.log('\n--- רשימת פוזיציות ---\n');

    positions.forEach((pos, i) => {
        console.log(`${i + 1}. ${pos.marketName}`);
        console.log(`   סוג: ${pos.type}`);
        if (pos.avgPrice) console.log(`   מחיר ממוצע: ${pos.avgPrice}`);
        if (pos.currentPrice) console.log(`   מחיר נוכחי: ${pos.currentPrice}`);
        if (pos.value) console.log(`   ערך: ${pos.value}`);
        if (pos.pnl) console.log(`   רווח/הפסד: ${pos.pnl}`);
        console.log('');
    });
}

// Main execution
(async () => {
    try {
        const { positions, userStats } = await scrapePolymarketPositions(USERNAME);
        analyzePositions(positions);

        console.log(`\n${'='.repeat(60)}`);
        console.log('החילוץ הושלם בהצלחה!');
        console.log(`הקבצים נשמרו בתיקייה: ${OUTPUT_DIR}`);
        console.log(`${'='.repeat(60)}\n`);

    } catch (error) {
        console.error('\nהחילוץ נכשל:', error.message);
        process.exit(1);
    }
})();
