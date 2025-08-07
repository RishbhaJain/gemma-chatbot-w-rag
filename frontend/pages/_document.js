import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="hi-en">
      <Head>
        {/* DNS Prefetch for performance */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="dns-prefetch" href="//fonts.gstatic.com" />
        
        {/* Preconnect for critical resources */}
        <link rel="preconnect" href="https://fonts.googleapis.com" crossOrigin="" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        
        {/* Critical CSS for Hindi fonts */}
        <style jsx>{`
          /* Critical font loading */
          @font-face {
            font-family: 'Noto Sans Devanagari';
            font-style: normal;
            font-weight: 400;
            font-display: swap;
            src: url(https://fonts.gstatic.com/s/notosansdevanagari/v20/TuGoUUFzXI5FBtUq5a8bjKYTZjtRU6Sgv3NaV_SNmI0b8QQCQmHn6B2OHjbL_08AlXQly_AzOy4.woff2) format('woff2');
            unicode-range: U+0900-097F, U+1CD0-1CF6, U+1CF8-1CF9, U+200C-200D, U+20A8, U+20B9, U+25CC, U+A830-A839, U+A8E0-A8FB;
          }
          
          @font-face {
            font-family: 'Inter';
            font-style: normal;
            font-weight: 400;
            font-display: swap;
            src: url(https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2) format('woff2');
            unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
          }
          
          /* Prevent flash of unstyled content */
          body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          }
          
          .font-hindi {
            font-family: 'Noto Sans Devanagari', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          }
        `}</style>
        
        {/* PWA Icons */}
        <link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/icons/favicon-16x16.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/icons/apple-touch-icon.png" />
        <link rel="mask-icon" href="/icons/safari-pinned-tab.svg" color="#3B82F6" />
        
        {/* Microsoft tiles */}
        <meta name="msapplication-TileColor" content="#3B82F6" />
        <meta name="msapplication-config" content="/icons/browserconfig.xml" />
        
        {/* Performance and Security */}
        <meta httpEquiv="x-dns-prefetch-control" content="on" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        
        {/* Audio/Microphone permissions hint */}
        <meta name="permissions-policy" content="microphone=*, camera=*, geolocation=()" />
      </Head>
      <body className="font-sans antialiased">
        {/* No-JS fallback */}
        <noscript>
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: '#f3f4f6',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: '2rem'
          }}>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
                JavaScript Required / JavaScript आवश्यक है
              </h1>
              <p style={{ marginBottom: '1rem' }}>
                This application requires JavaScript to function properly.
              </p>
              <p>
                इस एप्लिकेशन को सही तरीके से काम करने के लिए JavaScript की आवश्यकता है।
              </p>
            </div>
          </div>
        </noscript>
        
        {/* Main app content */}
        <Main />
        
        {/* Next.js scripts */}
        <NextScript />
        
        {/* Service Worker Registration */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function () {
                  navigator.serviceWorker.register('/sw.js').then(function (registration) {
                    console.log('SW registered: ', registration);
                  }).catch(function (registrationError) {
                    console.log('SW registration failed: ', registrationError);
                  });
                });
              }
            `,
          }}
        />
        
        {/* Performance monitoring */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Web Vitals monitoring
              if (typeof window !== 'undefined') {
                window.addEventListener('load', () => {
                  if ('performance' in window) {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    if (navigation) {
                      console.log('Page Load Time:', navigation.loadEventEnd - navigation.loadEventStart, 'ms');
                    }
                  }
                });
              }
            `,
          }}
        />
      </body>
    </Html>
  );
} 