import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import FullApp from '../FullApp';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00ff88' },
    secondary: { main: '#ff4444' },
    background: { default: '#0a0a0a', paper: '#1a1a1a' },
  },
});

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('SirHiss Trading Platform', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('renders main dashboard', async () => {
    // Mock API responses
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 404
      }) // bots API fails, should use demo data
      .mockResolvedValueOnce({
        ok: false,
        status: 404
      }); // portfolio API fails, should use demo data

    renderWithTheme(<FullApp />);

    // Check if main title is present
    expect(screen.getByText('🐍 SirHiss Trading Platform')).toBeInTheDocument();

    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    // Check portfolio cards
    expect(screen.getByText('Portfolio Value')).toBeInTheDocument();
    expect(screen.getByText('Available Cash')).toBeInTheDocument();
    expect(screen.getByText('Active Bots')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
  });

  test('navigation between sections works', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    // Navigate to Trading Bots
    fireEvent.click(screen.getByText('Trading Bots'));
    await waitFor(() => {
      expect(screen.getByText('🤖 Trading Bots')).toBeInTheDocument();
    });

    // Navigate to Algorithm Management
    fireEvent.click(screen.getByText('Algorithms'));
    await waitFor(() => {
      expect(screen.getByText('🔬 Algorithm Management')).toBeInTheDocument();
    });

    // Navigate to Portfolio
    fireEvent.click(screen.getByText('Portfolio'));
    await waitFor(() => {
      expect(screen.getByText('💼 Portfolio')).toBeInTheDocument();
    });
  });

  test('displays demo bot data when API fails', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    // Navigate to bots section
    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Trading Bots'));

    await waitFor(() => {
      expect(screen.getByText('Tech Growth Bot')).toBeInTheDocument();
      expect(screen.getByText('Dividend Hunter')).toBeInTheDocument();
      expect(screen.getByText('Grid Trader')).toBeInTheDocument();
    });
  });

  test('bot start/stop functionality', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    // Navigate to bots section and wait for load
    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Trading Bots'));

    await waitFor(() => {
      expect(screen.getByText('Grid Trader')).toBeInTheDocument();
    });

    // Find and click the Start button for the stopped bot
    const startButtons = screen.getAllByText('Start');
    expect(startButtons.length).toBeGreaterThan(0);

    fireEvent.click(startButtons[0]);

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/Bot started \(demo mode\)/)).toBeInTheDocument();
    });
  });

  test('algorithm management interface', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    // Navigate to algorithms
    fireEvent.click(screen.getByText('Algorithms'));

    await waitFor(() => {
      expect(screen.getByText('🔬 Algorithm Management')).toBeInTheDocument();
    });

    // Should show "No algorithms configured" initially
    expect(screen.getByText('No algorithms configured')).toBeInTheDocument();
    expect(screen.getByText('Add your first algorithm to start automated trading')).toBeInTheDocument();

    // Check algorithm templates tab
    fireEvent.click(screen.getByText('Algorithm Templates'));

    await waitFor(() => {
      expect(screen.getByText('RSI Technical Analysis')).toBeInTheDocument();
      expect(screen.getByText('Grid Trading')).toBeInTheDocument();
      expect(screen.getByText('DCA Strategy')).toBeInTheDocument();
      expect(screen.getByText('Trend Following')).toBeInTheDocument();
    });
  });

  test('sidebar toggle functionality', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    // Find the menu button and click it
    const menuButton = screen.getByLabelText(/open drawer/i);
    fireEvent.click(menuButton);

    // The sidebar should still be functional (this is more of a visual test)
    expect(screen.getByText('Trading Bots')).toBeInTheDocument();
  });

  test('portfolio metrics display correctly', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    await waitFor(() => {
      expect(screen.getByText('$15,750.25')).toBeInTheDocument(); // Portfolio value
      expect(screen.getByText('$2,250.75')).toBeInTheDocument();  // Available cash
      expect(screen.getByText('2 / 3')).toBeInTheDocument();      // Active bots
      expect(screen.getByText('+2.45%')).toBeInTheDocument();     // Performance
    });
  });

  test('handles API success responses', async () => {
    const mockBotsResponse = [
      {
        id: 1,
        name: 'API Test Bot',
        description: 'Bot from API',
        status: 'running',
        allocated_percentage: 50,
        current_value: 5000,
        allocated_amount: 4800
      }
    ];

    const mockPortfolioResponse = {
      total_value: 20000,
      total_pnl: 500,
      available_cash: 3000,
      active_bots: 1
    };

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockBotsResponse
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockPortfolioResponse
      });

    renderWithTheme(<FullApp />);

    await waitFor(() => {
      expect(screen.getByText('$20,000.00')).toBeInTheDocument(); // API portfolio value
    });

    // Navigate to bots to see API bot data
    fireEvent.click(screen.getByText('Trading Bots'));

    await waitFor(() => {
      expect(screen.getByText('API Test Bot')).toBeInTheDocument();
    });
  });

  test('error handling and user feedback', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    // Navigate to bots and try to start one
    fireEvent.click(screen.getByText('Trading Bots'));

    await waitFor(() => {
      expect(screen.getByText('Grid Trader')).toBeInTheDocument();
    });

    const startButtons = screen.getAllByText('Start');
    fireEvent.click(startButtons[0]);

    // Should show demo mode message
    await waitFor(() => {
      expect(screen.getByText(/demo mode/)).toBeInTheDocument();
    });
  });
});

describe('Algorithm Management Features', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  test('algorithm templates are displayed correctly', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    fireEvent.click(screen.getByText('Algorithms'));
    fireEvent.click(screen.getByText('Algorithm Templates'));

    await waitFor(() => {
      expect(screen.getByText('RSI Technical Analysis')).toBeInTheDocument();
      expect(screen.getByText('AdvancedTechnicalIndicator')).toBeInTheDocument();
      expect(screen.getByText('GridTrading')).toBeInTheDocument();
      expect(screen.getByText('DynamicDCA')).toBeInTheDocument();
    });

    // Check use template buttons
    const useTemplateButtons = screen.getAllByText('Use Template');
    expect(useTemplateButtons.length).toBe(4);
  });

  test('algorithm selection from bot interface', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    fireEvent.click(screen.getByText('Trading Bots'));

    await waitFor(() => {
      expect(screen.getByText('Tech Growth Bot')).toBeInTheDocument();
    });

    // Click the Algorithms button for a bot
    const algorithmButtons = screen.getAllByText('Algorithms');
    fireEvent.click(algorithmButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('🔬 Algorithm Management')).toBeInTheDocument();
      expect(screen.getByText('Bot ID: 1')).toBeInTheDocument();
    });
  });
});

describe('Responsive Design and Accessibility', () => {
  test('sidebar is responsive', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    renderWithTheme(<FullApp />);

    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    });

    // Check that navigation items are accessible
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Trading Bots')).toBeInTheDocument();
    expect(screen.getByText('Algorithms')).toBeInTheDocument();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('loading states are handled', async () => {
    // Mock a slow API response
    mockFetch.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ ok: false, status: 404 }), 100)
      )
    );

    renderWithTheme(<FullApp />);

    // Should show loading indicator
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('📊 Trading Dashboard')).toBeInTheDocument();
    }, { timeout: 2000 });
  });
});