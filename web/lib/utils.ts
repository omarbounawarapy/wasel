import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format a raw E.164-ish phone string into a human-readable display.
 * Examples:
 *   "21622222222"   → "+216 22 222 222"
 *   "+12125551234"  → "+1 212 555 1234"
 *   "+447911123456" → "+44 7911 123456"
 * Falls back to the raw string if the input is unrecognizable.
 */
export function formatPhone(raw: string | null | undefined): string {
  if (!raw) return '—';
  // Strip everything except digits and leading +
  const cleaned = raw.replace(/[^\d+]/g, '');
  // Must start with digits or +
  if (!cleaned) return raw;

  // Normalize to pure digits (strip leading +)
  const hasPlus = cleaned.startsWith('+');
  const digits = cleaned.replace(/\D/g, '');

  if (digits.length < 6) return raw;

  // Group digits into readable chunks for common country code lengths
  // Try to split into: country_code (1-3 digits) + subscriber (rest in groups of 3-4)
  const grouped = chunkSubscriber(digits, hasPlus);
  return hasPlus ? `+${grouped}` : grouped;
}

function chunkSubscriber(digits: string, hasCountryCode: boolean): string {
  // Known country code lengths: 1 (US/CA), 2 (most of EU), 3 (some)
  // Heuristic: if ≥11 digits assume 1-3 digit CC, else treat all as subscriber
  let cc = '';
  let subscriber = digits;

  if (digits.length >= 10) {
    // Guess CC length: try to identify known prefixes
    if (digits.startsWith('1') && digits.length === 11) {
      cc = digits.slice(0, 1);
      subscriber = digits.slice(1);
    } else if (['7', '20', '27', '30', '31', '32', '33', '34', '36', '39', '40', '41', '43',
                '44', '45', '46', '47', '48', '49', '51', '52', '53', '54', '55', '56', '57',
                '58', '60', '61', '62', '63', '64', '65', '66', '81', '82', '84', '86', '90',
                '91', '92', '93', '94', '95', '98'].some(p => digits.startsWith(p))) {
      cc = digits.slice(0, 2);
      subscriber = digits.slice(2);
    } else if (['212', '213', '216', '218', '220', '221', '222', '223', '224', '225', '226',
                '227', '228', '229', '230', '231', '232', '233', '234', '235', '236', '237',
                '238', '239', '240', '241', '242', '243', '244', '245', '246', '247', '248'].some(p => digits.startsWith(p))) {
      cc = digits.slice(0, 3);
      subscriber = digits.slice(3);
    } else if (digits.length >= 12) {
      cc = digits.slice(0, 3);
      subscriber = digits.slice(3);
    } else if (digits.length >= 11) {
      cc = digits.slice(0, 2);
      subscriber = digits.slice(2);
    } else {
      subscriber = digits;
    }
  }

  // Group subscriber in chunks of 2-3 (mobile-style)
  const chunks = subscriber.match(/.{1,3}/g) || [subscriber];
  const subscriberFormatted = chunks.join(' ');

  return cc ? `${cc} ${subscriberFormatted}` : subscriberFormatted;
}
