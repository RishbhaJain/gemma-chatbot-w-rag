import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import '../styles/globals.css';

// PWA install prompt handling
function useInstallPrompt() {
  const [installPromptEvent, setInstallPromptEvent] = useState(null);
  const [isInstallable, setIsInstallable] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (event) => {
      event.preventDefault();
      setInstallPromptEvent(event);
      setIsInstallable(true);
    };

    const handleAppInstalled = () => {
      setInstallPromptEvent(null);
      setIsInstallable(false);
      console.log('PWA was installed');
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const promptInstall = async () => {
    if (!installPromptEvent) return false;

    installPromptEvent.prompt();
    const { outcome } = await installPromptEvent.userChoice;
    
    if (outcome === 'accepted') {
      setInstallPromptEvent(null);
      setIsInstallable(false);
    }
    
    return outcome === 'accepted';
  };

  return { isInstallable, promptInstall };
}

// Service Worker registration
function useServiceWorker() {
  useEffect(() => {
    if (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      window.workbox !== undefined
    ) {
      const wb = window.workbox;
      
      // Add event listeners for service worker lifecycle
      wb.addEventListener('controlling', () => {
        window.location.reload();
      });

      wb.addEventListener('waiting', () => {
        // Show update available notification
        console.log('New app version available');
      });

      wb.register();
    }
  }, []);
}

// Performance monitoring
function usePerformanceMonitoring() {
  const router = useRouter();
  
  useEffect(() => {
    const handleRouteChangeStart = (url) => {
      console.log(`Route changing to: ${url}`);
    };

    const handleRouteChangeComplete = (url) => {
      console.log(`Route changed to: ${url}`);
      
      // Track page views (you can integrate analytics here)
      if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('config', 'GA_TRACKING_ID', {
          page_path: url,
        });
      }
    };

    router.events.on('routeChangeStart', handleRouteChangeStart);
    router.events.on('routeChangeComplete', handleRouteChangeComplete);

    return () => {
      router.events.off('routeChangeStart', handleRouteChangeStart);
      router.events.off('routeChangeComplete', handleRouteChangeComplete);
    };
  }, [router.events]);
}

export default function App({ Component, pageProps }) {
  const { isInstallable, promptInstall } = useInstallPrompt();
  useServiceWorker();
  usePerformanceMonitoring();

  // Provide global context
  const globalProps = {
    ...pageProps,
    pwa: {
      isInstallable,
      promptInstall,
    },
  };

  return (
    <>
      <Head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta
          name="viewport"
          content="width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no"
        />
        <meta name="description" content="Advanced Hinglish chatbot with voice processing" />
        <meta name="keywords" content="Hindi, English, Hinglish, Chatbot, Voice, AI, Speech Recognition" />
        
        {/* PWA Meta Tags */}
        <meta name="application-name" content="Hinglish Chatbot" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Hinglish Chatbot" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="theme-color" content="#3B82F6" />
        
        {/* Manifest */}
        <link rel="manifest" href="/manifest.json" />
        
        {/* Favicons */}
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
        
        {/* Preload critical resources */}
        <link
          rel="preload"
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@100;200;300;400;500;600;700;800;900&display=swap"
          as="style"
        />
        <link
          rel="preload"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&display=swap"
          as="style"
        />
        
        {/* Font Loading */}
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@100;200;300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </Head>
      
      {/* PWA Install Banner */}
      {isInstallable && (
        <div className="fixed top-0 left-0 right-0 bg-blue-600 text-white p-2 text-center z-50">
          <span className="text-sm mr-4">Install Hinglish Chatbot for better experience</span>
          <button
            onClick={promptInstall}
            className="bg-white text-blue-600 px-3 py-1 rounded text-sm font-medium hover:bg-gray-100 transition-colors"
          >
            Install
          </button>
        </div>
      )}
      
      {/* Main App */}
      <Component {...globalProps} />
    </>
  );
} 