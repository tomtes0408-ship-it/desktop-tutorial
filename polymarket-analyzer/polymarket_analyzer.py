#!/usr/bin/env python3
"""
Polymarket User Portfolio Analyzer
מנתח פורטפוליו של משתמשי Polymarket

This script fetches and analyzes user positions from Polymarket,
providing detailed insights into trading strategies, patterns, and performance.
"""

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import warnings
import sys
import os

# Hebrew font support
matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
warnings.filterwarnings('ignore')

# API Endpoints
GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"

class PolymarketAnalyzer:
    """Analyzer for Polymarket user portfolios and trading strategies."""

    def __init__(self, username: str):
        self.username = username
        self.wallet_address = None
        self.positions = []
        self.trades = []
        self.profile_data = {}

    def get_user_profile(self) -> dict:
        """Fetch user profile and wallet address from username."""
        print(f"מחפש פרופיל עבור: @{self.username}")

        # Try search endpoint first
        try:
            response = requests.get(
                f"{GAMMA_API}/public-search",
                params={"query": self.username, "type": "profile"},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    for profile in data:
                        if profile.get('pseudonym', '').lower() == self.username.lower():
                            self.wallet_address = profile.get('proxyWallet') or profile.get('address')
                            self.profile_data = profile
                            print(f"נמצא! כתובת ארנק: {self.wallet_address}")
                            return profile
        except Exception as e:
            print(f"שגיאה בחיפוש: {e}")

        # Try direct profile lookup
        try:
            response = requests.get(
                f"{GAMMA_API}/profiles",
                params={"username": self.username},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    profile = data[0] if isinstance(data, list) else data
                    self.wallet_address = profile.get('proxyWallet') or profile.get('address')
                    self.profile_data = profile
                    print(f"נמצא! כתובת ארנק: {self.wallet_address}")
                    return profile
        except Exception as e:
            print(f"שגיאה בחיפוש ישיר: {e}")

        return {}

    def get_positions(self) -> list:
        """Fetch all user positions from Data API."""
        if not self.wallet_address:
            print("שגיאה: לא נמצאה כתובת ארנק")
            return []

        print(f"מוריד פוזיציות...")
        all_positions = []

        try:
            # Get current positions
            response = requests.get(
                f"{DATA_API}/positions",
                params={
                    "user": self.wallet_address,
                    "sortBy": "CURRENT",
                    "sortDirection": "DESC"
                },
                timeout=60
            )
            if response.status_code == 200:
                positions = response.json()
                if positions:
                    all_positions.extend(positions)
                    print(f"נמצאו {len(positions)} פוזיציות פתוחות")
        except Exception as e:
            print(f"שגיאה בהורדת פוזיציות: {e}")

        # Get closed positions
        try:
            response = requests.get(
                f"{DATA_API}/closed-positions",
                params={
                    "user": self.wallet_address,
                    "sortBy": "INITIAL",
                    "sortDirection": "DESC"
                },
                timeout=60
            )
            if response.status_code == 200:
                closed = response.json()
                if closed:
                    for pos in closed:
                        pos['status'] = 'closed'
                    all_positions.extend(closed)
                    print(f"נמצאו {len(closed)} פוזיציות סגורות")
        except Exception as e:
            print(f"שגיאה בהורדת פוזיציות סגורות: {e}")

        self.positions = all_positions
        return all_positions

    def get_trades(self) -> list:
        """Fetch user trade history."""
        if not self.wallet_address:
            return []

        print("מוריד היסטוריית עסקאות...")

        try:
            response = requests.get(
                f"{DATA_API}/trades",
                params={
                    "user": self.wallet_address,
                    "limit": 1000
                },
                timeout=60
            )
            if response.status_code == 200:
                trades = response.json()
                self.trades = trades if trades else []
                print(f"נמצאו {len(self.trades)} עסקאות")
                return self.trades
        except Exception as e:
            print(f"שגיאה בהורדת עסקאות: {e}")

        return []

    def get_activity(self) -> list:
        """Fetch user activity history."""
        if not self.wallet_address:
            return []

        print("מוריד פעילות משתמש...")
        activities = []

        try:
            response = requests.get(
                f"{DATA_API}/activity",
                params={
                    "user": self.wallet_address,
                    "limit": 500
                },
                timeout=60
            )
            if response.status_code == 200:
                activities = response.json() or []
                print(f"נמצאו {len(activities)} פעילויות")
        except Exception as e:
            print(f"שגיאה בהורדת פעילות: {e}")

        return activities

    def analyze_positions(self) -> pd.DataFrame:
        """Convert positions to DataFrame with analysis."""
        if not self.positions:
            return pd.DataFrame()

        data = []
        for pos in self.positions:
            try:
                # Extract market info
                market_name = pos.get('title', pos.get('question', 'לא ידוע'))
                outcome = pos.get('outcome', pos.get('side', 'Unknown'))

                # Calculate values
                size = float(pos.get('size', pos.get('tokens', 0)))
                avg_price = float(pos.get('avgPrice', pos.get('averagePrice', 0)))
                current_price = float(pos.get('currentPrice', pos.get('price', 0)))

                initial_value = size * avg_price
                current_value = size * current_price
                pnl = current_value - initial_value
                pnl_percent = (pnl / initial_value * 100) if initial_value > 0 else 0

                # Get dates
                created = pos.get('createdAt', pos.get('timestamp', ''))

                data.append({
                    'שם השוק': market_name[:80] + '...' if len(market_name) > 80 else market_name,
                    'תאריך': created[:10] if created else 'לא ידוע',
                    'סוג': 'Yes' if outcome.lower() in ['yes', 'true', '1'] else 'No',
                    'כמות': round(size, 2),
                    'מחיר ממוצע': f"${avg_price:.3f}",
                    'מחיר נוכחי': f"${current_price:.3f}",
                    'השקעה ראשונית': f"${initial_value:.2f}",
                    'ערך נוכחי': f"${current_value:.2f}",
                    'רווח/הפסד': f"${pnl:.2f}",
                    'רווח %': f"{pnl_percent:.1f}%",
                    'סטטוס': pos.get('status', 'פתוח'),
                    'raw_pnl': pnl,
                    'raw_initial': initial_value,
                    'raw_current': current_value,
                    'raw_avg_price': avg_price,
                    'raw_current_price': current_price
                })
            except Exception as e:
                continue

        return pd.DataFrame(data)

    def generate_analysis_report(self, df: pd.DataFrame) -> str:
        """Generate comprehensive Hebrew analysis report."""
        if df.empty:
            return "לא נמצאו נתונים לניתוח"

        report = []
        report.append("=" * 80)
        report.append(f"ניתוח פורטפוליו עבור: @{self.username}")
        report.append(f"תאריך הניתוח: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 80)

        # Portfolio Summary
        total_invested = df['raw_initial'].sum()
        total_current = df['raw_current'].sum()
        total_pnl = df['raw_pnl'].sum()
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0

        report.append("\n📊 סיכום פורטפוליו")
        report.append("-" * 40)
        report.append(f"סה\"כ פוזיציות: {len(df)}")
        report.append(f"סה\"כ השקעה: ${total_invested:,.2f}")
        report.append(f"ערך נוכחי: ${total_current:,.2f}")
        report.append(f"רווח/הפסד כולל: ${total_pnl:,.2f} ({total_pnl_percent:.1f}%)")

        # Win/Loss Analysis
        winning = df[df['raw_pnl'] > 0]
        losing = df[df['raw_pnl'] < 0]
        neutral = df[df['raw_pnl'] == 0]

        win_rate = (len(winning) / len(df) * 100) if len(df) > 0 else 0

        report.append(f"\n🎯 ניתוח הצלחה")
        report.append("-" * 40)
        report.append(f"פוזיציות מרוויחות: {len(winning)} ({win_rate:.1f}%)")
        report.append(f"פוזיציות מפסידות: {len(losing)}")
        report.append(f"פוזיציות נייטרליות: {len(neutral)}")

        if len(winning) > 0:
            avg_win = winning['raw_pnl'].mean()
            max_win = winning['raw_pnl'].max()
            report.append(f"רווח ממוצע: ${avg_win:.2f}")
            report.append(f"רווח מקסימלי: ${max_win:.2f}")

        if len(losing) > 0:
            avg_loss = losing['raw_pnl'].mean()
            max_loss = losing['raw_pnl'].min()
            report.append(f"הפסד ממוצע: ${avg_loss:.2f}")
            report.append(f"הפסד מקסימלי: ${max_loss:.2f}")

        # Position Type Analysis
        yes_positions = df[df['סוג'] == 'Yes']
        no_positions = df[df['סוג'] == 'No']

        report.append(f"\n📈 ניתוח סוגי פוזיציות")
        report.append("-" * 40)
        report.append(f"פוזיציות Yes: {len(yes_positions)} ({len(yes_positions)/len(df)*100:.1f}%)")
        report.append(f"פוזיציות No: {len(no_positions)} ({len(no_positions)/len(df)*100:.1f}%)")

        if len(yes_positions) > 0:
            yes_pnl = yes_positions['raw_pnl'].sum()
            report.append(f"רווח/הפסד מ-Yes: ${yes_pnl:.2f}")

        if len(no_positions) > 0:
            no_pnl = no_positions['raw_pnl'].sum()
            report.append(f"רווח/הפסד מ-No: ${no_pnl:.2f}")

        # Price Analysis
        report.append(f"\n💰 ניתוח מחירים")
        report.append("-" * 40)
        avg_entry_price = df['raw_avg_price'].mean()
        avg_current_price = df['raw_current_price'].mean()
        report.append(f"מחיר כניסה ממוצע: ${avg_entry_price:.3f}")
        report.append(f"מחיר נוכחי ממוצע: ${avg_current_price:.3f}")

        # Price range preference
        low_price = df[df['raw_avg_price'] < 0.30]
        mid_price = df[(df['raw_avg_price'] >= 0.30) & (df['raw_avg_price'] <= 0.70)]
        high_price = df[df['raw_avg_price'] > 0.70]

        report.append(f"\nהתפלגות מחירי כניסה:")
        report.append(f"  מחירים נמוכים (<30%): {len(low_price)} ({len(low_price)/len(df)*100:.1f}%)")
        report.append(f"  מחירים בינוניים (30-70%): {len(mid_price)} ({len(mid_price)/len(df)*100:.1f}%)")
        report.append(f"  מחירים גבוהים (>70%): {len(high_price)} ({len(high_price)/len(df)*100:.1f}%)")

        # Strategy Analysis
        report.append(f"\n🧠 ניתוח אסטרטגיה")
        report.append("-" * 40)

        # Determine strategy type
        if avg_entry_price < 0.30:
            strategy = "אסטרטגיית Long-shot - מעדיף הימורים בסיכוי נמוך עם פוטנציאל רווח גבוה"
        elif avg_entry_price > 0.70:
            strategy = "אסטרטגיית Safe Bet - מעדיף הימורים בטוחים עם סיכוי גבוה לזכייה"
        else:
            strategy = "אסטרטגיית מאוזנת - משלב בין הימורים בטוחים לספקולטיביים"

        report.append(f"סוג אסטרטגיה: {strategy}")

        # Risk assessment
        volatility = df['raw_pnl'].std() if len(df) > 1 else 0
        avg_position_size = df['raw_initial'].mean()

        if avg_position_size > 100:
            size_profile = "שחקן גדול - פוזיציות גדולות"
        elif avg_position_size > 20:
            size_profile = "שחקן בינוני - פוזיציות מתונות"
        else:
            size_profile = "שחקן קטן - פוזיציות קטנות"

        report.append(f"פרופיל גודל: {size_profile}")
        report.append(f"גודל פוזיציה ממוצע: ${avg_position_size:.2f}")
        report.append(f"סטיית תקן רווחים: ${volatility:.2f}")

        # Top positions
        report.append(f"\n🏆 טובות 5 הפוזיציות")
        report.append("-" * 40)
        top_5 = df.nlargest(5, 'raw_pnl')
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            report.append(f"{i}. {row['שם השוק']}")
            report.append(f"   רווח: {row['רווח/הפסד']} | סוג: {row['סוג']}")

        # Worst positions
        report.append(f"\n📉 5 הפוזיציות הגרועות")
        report.append("-" * 40)
        bottom_5 = df.nsmallest(5, 'raw_pnl')
        for i, (_, row) in enumerate(bottom_5.iterrows(), 1):
            report.append(f"{i}. {row['שם השוק']}")
            report.append(f"   הפסד: {row['רווח/הפסד']} | סוג: {row['סוג']}")

        # Conclusions
        report.append(f"\n📝 סיכום והמלצות")
        report.append("-" * 40)

        if win_rate > 60:
            report.append("✅ אחוז הצלחה גבוה - המשתמש מדויק בתחזיות שלו")
        elif win_rate > 40:
            report.append("⚖️ אחוז הצלחה ממוצע - יש מקום לשיפור בבחירת שווקים")
        else:
            report.append("⚠️ אחוז הצלחה נמוך - מומלץ לבחון מחדש את האסטרטגיה")

        if total_pnl > 0:
            report.append(f"✅ הפורטפוליו רווחי - סה\"כ ${total_pnl:.2f}")
        else:
            report.append(f"⚠️ הפורטפוליו מפסיד - סה\"כ ${total_pnl:.2f}")

        report.append("=" * 80)

        return "\n".join(report)

    def create_visualizations(self, df: pd.DataFrame, output_dir: str = "."):
        """Create visualization charts."""
        if df.empty:
            print("אין נתונים ליצירת גרפים")
            return

        print("יוצר תרשימים...")

        # Set up the figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        fig.suptitle(f'Polymarket Portfolio Analysis - @{self.username}', fontsize=16, fontweight='bold')

        # 1. PnL Distribution
        ax1 = axes[0, 0]
        colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in df['raw_pnl']]
        ax1.bar(range(len(df)), df['raw_pnl'], color=colors, alpha=0.7)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.set_title('PnL Distribution by Position')
        ax1.set_xlabel('Position #')
        ax1.set_ylabel('PnL ($)')
        ax1.grid(True, alpha=0.3)

        # 2. Position Type Pie Chart
        ax2 = axes[0, 1]
        type_counts = df['סוג'].value_counts()
        colors_pie = ['#2ecc71', '#e74c3c']
        ax2.pie(type_counts.values, labels=['Yes', 'No'][:len(type_counts)],
                autopct='%1.1f%%', colors=colors_pie[:len(type_counts)], startangle=90)
        ax2.set_title('Position Types Distribution')

        # 3. Entry Price Distribution
        ax3 = axes[1, 0]
        ax3.hist(df['raw_avg_price'], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        ax3.axvline(df['raw_avg_price'].mean(), color='red', linestyle='--', label=f'Mean: ${df["raw_avg_price"].mean():.3f}')
        ax3.set_title('Entry Price Distribution')
        ax3.set_xlabel('Entry Price ($)')
        ax3.set_ylabel('Count')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Win/Loss Summary
        ax4 = axes[1, 1]
        winning = len(df[df['raw_pnl'] > 0])
        losing = len(df[df['raw_pnl'] < 0])
        neutral = len(df[df['raw_pnl'] == 0])

        bars = ax4.bar(['Winning', 'Losing', 'Neutral'], [winning, losing, neutral],
                      color=['#2ecc71', '#e74c3c', '#95a5a6'])
        ax4.set_title('Win/Loss Distribution')
        ax4.set_ylabel('Number of Positions')

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax4.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        ax4.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        # Save the figure
        output_path = os.path.join(output_dir, f'portfolio_analysis_{self.username}.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"תרשים נשמר: {output_path}")
        plt.close()

        # Create additional chart - Cumulative PnL
        fig2, ax = plt.subplots(figsize=(12, 6))
        cumulative_pnl = df['raw_pnl'].cumsum()
        ax.plot(range(len(cumulative_pnl)), cumulative_pnl, 'b-', linewidth=2)
        ax.fill_between(range(len(cumulative_pnl)), cumulative_pnl, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title(f'Cumulative PnL Over Positions - @{self.username}')
        ax.set_xlabel('Position #')
        ax.set_ylabel('Cumulative PnL ($)')
        ax.grid(True, alpha=0.3)

        output_path2 = os.path.join(output_dir, f'cumulative_pnl_{self.username}.png')
        plt.savefig(output_path2, dpi=150, bbox_inches='tight')
        print(f"תרשים מצטבר נשמר: {output_path2}")
        plt.close()

    def export_data(self, df: pd.DataFrame, output_dir: str = "."):
        """Export data to various formats."""
        if df.empty:
            return

        # Export to CSV
        csv_cols = ['שם השוק', 'תאריך', 'סוג', 'כמות', 'מחיר ממוצע', 'מחיר נוכחי',
                   'השקעה ראשונית', 'ערך נוכחי', 'רווח/הפסד', 'רווח %', 'סטטוס']
        export_df = df[csv_cols]

        csv_path = os.path.join(output_dir, f'positions_{self.username}.csv')
        export_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"נתונים יוצאו ל: {csv_path}")

        # Export to JSON
        json_path = os.path.join(output_dir, f'positions_{self.username}.json')
        export_df.to_json(json_path, orient='records', force_ascii=False, indent=2)
        print(f"נתונים יוצאו ל: {json_path}")

    def run_full_analysis(self, output_dir: str = "."):
        """Run complete analysis pipeline."""
        print("\n" + "=" * 60)
        print(f"מתחיל ניתוח מלא עבור @{self.username}")
        print("=" * 60 + "\n")

        # Step 1: Get user profile
        profile = self.get_user_profile()
        if not self.wallet_address:
            print("\n❌ לא ניתן למצוא את המשתמש. ודא שהשם נכון.")
            return None

        # Step 2: Get positions
        positions = self.get_positions()
        if not positions:
            print("\n❌ לא נמצאו פוזיציות למשתמש זה")
            return None

        # Step 3: Get trades
        self.get_trades()

        # Step 4: Analyze positions
        df = self.analyze_positions()

        # Step 5: Generate report
        report = self.generate_analysis_report(df)
        print("\n" + report)

        # Save report
        report_path = os.path.join(output_dir, f'analysis_report_{self.username}.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nדוח נשמר ב: {report_path}")

        # Step 6: Create visualizations
        self.create_visualizations(df, output_dir)

        # Step 7: Export data
        self.export_data(df, output_dir)

        return df


def main():
    """Main entry point."""
    # Default username
    username = "anoin123"

    # Check command line arguments
    if len(sys.argv) > 1:
        username = sys.argv[1].replace('@', '')

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Initialize analyzer
    analyzer = PolymarketAnalyzer(username)

    # Run full analysis
    df = analyzer.run_full_analysis(output_dir)

    if df is not None:
        print("\n" + "=" * 60)
        print("✅ הניתוח הושלם בהצלחה!")
        print("=" * 60)

        # Print positions table
        print("\n📋 טבלת פוזיציות מלאה:")
        print("-" * 100)
        display_cols = ['שם השוק', 'סוג', 'מחיר ממוצע', 'מחיר נוכחי', 'רווח/הפסד']
        print(df[display_cols].to_string(index=False))
    else:
        print("\n❌ הניתוח נכשל. בדוק את שם המשתמש או נסה שוב מאוחר יותר.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
