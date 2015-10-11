#include <stdio.h>
#include <stdint.h>

#include "stm32f4xx_conf.h"
#include "stm32f4xx.h"

#include "usbd_core.h"
#include "usbd_usr.h"
#include "usbd_desc.h"
#include "usbd_cdc_vcp.h"

#include "console.h"
#include "galvo.h"

#define BLINK_DELAY_MS	(500)

volatile uint32_t tickMs = 0;
__ALIGN_BEGIN USB_OTG_CORE_HANDLE  USB_OTG_dev __ALIGN_END;

// Private function prototypes
void Delay(volatile uint32_t nCount);
void init();

#define XOFFMAX (500)
#define XOFFMIN (-50)
#define YOFFMAX (500)
#define YOFFMIN (-50)

typedef struct {
	uint16_t x;
	uint16_t y;
} path_t;

path_t path0[] = {{1938, 1896},{1938, 1896},{1938, 1896}, {1872, 1906}, {1865, 1906}, {1865, 1911}, {1828, 1911}, {1806, 1911}, {1791, 1901}, {1761, 1885}, {1754, 1870}, {1747, 1864}, {1747, 1859}, {1739, 1859}, {1739, 1854}, {1732, 1849}, {1725, 1838}, {1717, 1833}, {1717, 1823}, {1710, 1818}, {1710, 1812}, {1703, 1802}, {1703, 1797}, {1695, 1786}, {1695, 1760}, {1688, 1755}, {1688, 1750}, {1688, 1739}, {1680, 1734}, {1680, 1708}, {1680, 1661}, {1680, 1614}, {1680, 1604}, {1680, 1599}, {1688, 1588}, {1688, 1562}, {1695, 1557}, {1695, 1552}, {1703, 1552}, {1717, 1541}, {1725, 1541}, {1732, 1536}, {1739, 1531}, {1739, 1526}, {1754, 1526}, {1754, 1520}, {1769, 1520}, {1776, 1515}, {1791, 1515}, {1806, 1510}, {1820, 1510}, {1828, 1505}, {1850, 1505}, {1894, 1505}, {1990, 1505}, {2027, 1505}, {2027, 1510}, {2034, 1510}, {2034, 1515}, {2056, 1515}, {2064, 1520}, {2071, 1520}, {2086, 1526}, {2101, 1526}, {2108, 1531}, {2115, 1531}, {2137, 1541}, {2167, 1552}, {2174, 1562}, {2189, 1567}, {2189, 1573}, {2196, 1578}, {2204, 1588}, {2211, 1593}, {2241, 1614}, {2248, 1625}, {2255, 1630}, {2255, 1640}, {2263, 1661}, {2263, 1672}, {2270, 1677}, {2270, 1687}, {2278, 1692}, {2285, 1703}, {2300, 1713}, {2300, 1718}, {2307, 1729}, {2307, 1739}, {2307, 1776}, {2307, 1797}, {2292, 1807}, {2285, 1812}, {2278, 1812}, {2278, 1818}, {2270, 1818}, {2263, 1823}, {2255, 1823}, {2248, 1828}, {2241, 1828}, {2233, 1833}, {2226, 1833}, {2226, 1838}, {2219, 1838}, {2196, 1849}, {2189, 1849}, {2174, 1859}, {2160, 1859}, {2160, 1864}, {2152, 1864}, {2137, 1870}, {2130, 1870}, {2123, 1880}, {2093, 1880}, {2078, 1885}, {2056, 1885}, {1990, 1885}, {1968, 1885}, {1938, 1896}, {1909, 1896}, {1902, 1896}, {1902, 1901}, {1894, 1901}, {1894, 1906}, {1894, 1937}, {1887, 1974}, {1887, 2010}, {1887, 2021}, {1879, 2031}, {1879, 2042}, {1879, 2073}, {1879, 2156}, {1879, 2188}, {1872, 2198}, {1872, 2235}, {1872, 2308}, {1872, 2344}, {1872, 2360}, {1865, 2381}, {1887, 2448}, {1902, 2495}, {1924, 2547}, {1931, 2563}, {1931, 2573}, {1938, 2594}, {1938, 2631}, {1946, 2662}, {1946, 2719}, {1946, 2730}, {1953, 2730}, {1953, 2740}, {1953, 2745}, {1953, 2740}, {1953, 2730}, {1953, 2704}, {1953, 2693}, {1938, 2662}, {1924, 2631}, {1916, 2579}, {1916, 2568}, {1909, 2563}, {1902, 2553}, {1902, 2542}, {1894, 2532}, {1894, 2526}, {1894, 2506}, {1887, 2500}, {1887, 2474}, {1872, 2464}, {1865, 2453}, {1865, 2448}, {1857, 2448}, {1857, 2443}, {1857, 2433}, {1857, 2422}, {1857, 2417}, {1857, 2422}, {1850, 2443}, {1806, 2506}, {1791, 2532}, {1769, 2553}, {1754, 2579}, {1739, 2599}, {1725, 2626}, {1710, 2652}, {1703, 2672}, {1695, 2688}, {1673, 2730}, {1666, 2735}, {1644, 2751}, {1644, 2745}, {1644, 2740}, {1666, 2683}, {1695, 2652}, {1703, 2636}, {1717, 2610}, {1732, 2563}, {1739, 2547}, {1747, 2532}, {1754, 2521}, {1761, 2516}, {1776, 2485}, {1791, 2464}, {1791, 2443}, {1798, 2422}, {1798, 2386}, {1798, 2381}, {1806, 2370}, {1806, 2344}, {1813, 2339}, {1813, 2328}, {1813, 2313}, {1813, 2302}, {1820, 2297}, {1820, 2276}, {1835, 2271}, {1835, 2266}, {1843, 2266}, {1857, 2266}, {1857, 2255}, {1865, 2250}, {1865, 2235}, {1865, 2198}, {1879, 2188}, {2189, 2188}, {2233, 2193}, {2255, 2193}, {2255, 2198}, {2263, 2198}, {2270, 2198}, {2278, 2198}, {2137, 2198}, {2078, 2198}, {2056, 2198}, {2042, 2203}, {2027, 2203}, {1997, 2203}, {1902, 2203}, {1857, 2203}, {1850, 2203}, {1843, 2203}, {1835, 2198}, {1769, 2141}, {1747, 2130}, {1739, 2120}, {1710, 2099}, {1688, 2089}, {1688, 2083}, {1680, 2083}, {1673, 2078}, {1666, 2078}, {1651, 2073}, {1644, 2073}, {1629, 2068}, {1621, 2068}, {1614, 2068}, {1599, 2057}, {1592, 2057}, {1585, 2052}, {1577, 2052}, {1570, 2047}, {1562, 2047}, {1555, 2042}, {1533, 2042}, {1526, 2042}, {1540, 2052}, {1555, 2073}, {1562, 2073}, {1585, 2089}, {1592, 2089}, {1599, 2099}, {1607, 2104}, {1614, 2109}, {1621, 2109}, {1629, 2120}, {1636, 2120}, {1666, 2130}, {1680, 2136}, {1688, 2146}, {1710, 2162}, {1725, 2162}, {1739, 2167}, {1747, 2167}, {1747, 2172}, {1754, 2172}, {1761, 2177}, {1761, 2182}, {1784, 2182}, {1791, 2188}, {1820, 2188}, {1820, 2193}, {1843, 2193}, {1843, 2198}, };

static int16_t xOff, yOff;
static int8_t xSpd, ySpd;

static uint32_t pathIndex = 0;

void controlLoopInit() {
	xSpd = 20;
	ySpd = -24;

	TIM_TimeBaseInitTypeDef timerConfig;

	// Power the timer
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM9, ENABLE);

	//
	// Configure timer for 100us period
	//
	TIM_TimeBaseStructInit(&timerConfig);

	timerConfig.TIM_Period = 100;
	timerConfig.TIM_Prescaler = 168;
	timerConfig.TIM_ClockDivision = 0;
	timerConfig.TIM_CounterMode = TIM_CounterMode_Up;

	TIM_TimeBaseInit(TIM9, &timerConfig);

	TIM_ITConfig(TIM9, TIM_IT_Update, ENABLE);

	NVIC_EnableIRQ(TIM1_BRK_TIM9_IRQn);

	// Enable the timer!
	TIM_Cmd(TIM9, ENABLE);
}



void TIM1_BRK_TIM9_IRQHandler(void) {
	uint32_t sr = TIM9->SR;
	TIM9->SR &= ~sr;

	if(sr & TIM_FLAG_Update) {
		
		galvoSet(0, path0[pathIndex].x/2 + 256 + xOff);
		galvoSet(1, path0[pathIndex].y/2 + 256 + yOff);

		if(pathIndex == 10) {
			GPIO_SetBits(GPIOE, GPIO_Pin_4);
		}

		if(pathIndex < sizeof(path0)/sizeof(path_t)) {
			pathIndex++;
		} else {
			// Laser off?
			GPIO_ResetBits(GPIOE, GPIO_Pin_4);
		}
	}
}

#define MOVE_DELAY_MS (33)

int main(void) {
	uint32_t nextBlink;
	uint32_t nextMove;

	uint32_t blinkState = 0;
	init();

	// Disable line buffering on stdout
	setbuf(stdout, NULL);

	nextBlink = tickMs + BLINK_DELAY_MS;
	nextMove = tickMs + MOVE_DELAY_MS;
	for(;;) {

		consoleProcess();

		if(tickMs > nextBlink) {
			nextBlink = tickMs + BLINK_DELAY_MS;
			if(blinkState) {
				GPIO_SetBits(GPIOD, GPIO_Pin_12);
			} else {
				GPIO_ResetBits(GPIOD, GPIO_Pin_12);
			}
			blinkState ^= 1;
		}

		if(tickMs > nextMove) {
			nextMove = tickMs + MOVE_DELAY_MS;
			
			pathIndex = 0;

			xOff += xSpd;
			if(xOff >= XOFFMAX) {
				xOff = XOFFMAX;
				xSpd = -xSpd;
			} else if(xOff <= XOFFMIN) {
				xOff = XOFFMIN;
				xSpd = -xSpd;
			}

			yOff += ySpd;
			if(yOff >= YOFFMAX) {
				yOff = YOFFMAX;
				ySpd = -ySpd;
			} else if(yOff <= YOFFMIN) {
				yOff = YOFFMIN;
				ySpd = -ySpd;
			}

		}

		__WFI();
		
	}

	return 0;
}

void init() {

	// ---------- SysTick timer -------- //
	if (SysTick_Config(SystemCoreClock / 1000)) {
		// Capture error
		while (1){};
	}

	// ---------- GPIO -------- //
	// GPIOD Periph clock enable
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOD, ENABLE);

	GPIO_Init(GPIOD, &(GPIO_InitTypeDef){GPIO_Pin_12, GPIO_Mode_OUT, GPIO_Speed_2MHz, GPIO_OType_PP, GPIO_PuPd_NOPULL});
	GPIO_Init(GPIOD, &(GPIO_InitTypeDef){GPIO_Pin_14, GPIO_Mode_OUT, GPIO_Speed_2MHz, GPIO_OType_PP, GPIO_PuPd_NOPULL});

	consoleInit();

	USBD_Init(&USB_OTG_dev,
				USB_OTG_FS_CORE_ID,
				&USR_desc,
				&USBD_CDC_cb,
				&USR_cb);

	controlLoopInit();
}

void SysTick_Handler(void)
{
	tickMs++;
}
