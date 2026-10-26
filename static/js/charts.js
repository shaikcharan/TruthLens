/**
 * TruthLens Dashboard Chart Controller
 * Visualizes real SQLite metrics using Chart.js without external telemetry.
 * High-DPI crisp rendering, clear plain-English labels, and non-cramped layouts.
 */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js library not loaded.');
        return;
    }

    // Ensure high-DPI sharp rendering on Windows scaling (125%, 150%, 200%)
    Chart.defaults.devicePixelRatio = Math.max(window.devicePixelRatio || 1, 2);
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.color = '#334155';

    const stats = window.TRUTHLENS_STATS || {};

    // -------------------------------------------------------------
    // Chart 1: Persuasive Techniques Distribution (Horizontal Bar)
    // -------------------------------------------------------------
    const techniquesCanvas = document.getElementById('techniquesChart');
    if (techniquesCanvas && stats.techniques_distribution && stats.techniques_distribution.length > 0) {
        const labels = stats.techniques_distribution.map(item => item.technique);
        const counts = stats.techniques_distribution.map(item => item.count);

        new Chart(techniquesCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Times Detected',
                    data: counts,
                    backgroundColor: '#1e3a8a',
                    hoverBackgroundColor: '#2563eb',
                    borderColor: '#172554',
                    borderWidth: 1,
                    borderRadius: 4,
                    barPercentage: 0.7,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        titleFont: { size: 13, weight: '600' },
                        bodyFont: { size: 12 },
                        padding: 10,
                        displayColors: false,
                        callbacks: {
                            label: (ctx) => ` Detected ${ctx.raw} time(s) across stories`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            precision: 0,
                            font: { size: 12 }
                        },
                        grid: { color: '#f1f5f9' },
                        title: {
                            display: true,
                            text: 'Number of Occurrences',
                            font: { size: 12, weight: '600' },
                            color: '#64748b'
                        }
                    },
                    y: {
                        ticks: {
                            font: { size: 12, weight: '500' },
                            color: '#0f172a'
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // -------------------------------------------------------------
    // Chart 2: Factual Claim Fact-Check Results (Doughnut)
    // -------------------------------------------------------------
    const claimsCanvas = document.getElementById('claimsStatusChart');
    if (claimsCanvas && stats.status_distribution) {
        const statusMap = stats.status_distribution;
        const labels = Object.keys(statusMap);
        const counts = Object.values(statusMap);

        if (labels.length > 0 && counts.some(c => c > 0)) {
            // High-contrast, semantic status colors for both new and legacy statuses
            const colorMapping = {
                // New Plain-English Verdicts
                'Contradicted by evidence': '#ef4444',
                'Misleading or missing context': '#f59e0b',
                'Supported by evidence': '#10b981',
                'Mixed evidence': '#eab308',
                'Not yet verified': '#64748b',

                // Legacy fallback verdicts
                'Contradicted by available evidence': '#ef4444',
                'Partially supported': '#f59e0b',
                'Supported by available evidence': '#10b981',
                'Unverified': '#64748b',
                'Unable to analyze': '#94a3af'
            };

            const bgColors = labels.map(status => {
                // Direct lookup or fuzzy match
                const sLower = status.toLowerCase();
                if (sLower.includes('contradict')) return '#ef4444';
                if (sLower.includes('mislead') || sLower.includes('partially')) return '#f59e0b';
                if (sLower.includes('supported by') && !sLower.includes('partially')) return '#10b981';
                if (sLower.includes('mix')) return '#eab308';
                if (sLower.includes('unverified') || sLower.includes('not yet')) return '#64748b';
                return colorMapping[status] || '#94a3b8';
            });

            new Chart(claimsCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: bgColors,
                        borderWidth: 2,
                        borderColor: '#ffffff',
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 14,
                                font: { size: 12, weight: '500' },
                                padding: 12,
                                color: '#1e293b'
                            }
                        },
                        tooltip: {
                            titleFont: { size: 13, weight: '600' },
                            bodyFont: { size: 12 },
                            padding: 10,
                            callbacks: {
                                label: (ctx) => ` ${ctx.label}: ${ctx.raw} claim(s)`
                            }
                        }
                    },
                    cutout: '60%'
                }
            });
        }
    }
});
