// Simple test to verify login flow and dashboard data loading
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🚀 Testing SirHiss Login Flow...');
    
    // Navigate to login page
    await page.goto('http://localhost:9001');
    console.log('✅ Loaded login page');
    
    // Wait for login form to appear
    await page.waitForSelector('input[name="username"]', { timeout: 10000 });
    console.log('✅ Login form loaded');
    
    // Fill in admin credentials
    await page.type('input[name="username"]', 'admin');
    await page.type('input[name="password"]', 'admin123');
    console.log('✅ Filled credentials');
    
    // Click login button
    await page.click('button:contains("Sign In")');
    console.log('✅ Clicked login button');
    
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 15000 });
    console.log('✅ Dashboard loaded successfully');
    
    // Check for portfolio data
    const portfolioValue = await page.$eval('[data-testid="portfolio-value"]', el => el.textContent);
    console.log(`✅ Portfolio value displayed: ${portfolioValue}`);
    
    console.log('🎉 All tests passed! Login flow works correctly.');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
})();