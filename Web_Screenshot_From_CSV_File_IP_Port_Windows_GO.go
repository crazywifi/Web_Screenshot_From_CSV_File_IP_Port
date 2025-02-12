package main

import (
	"context"
	"encoding/csv"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/chromedp/chromedp"
	"github.com/xuri/excelize/v2"
)

const outputFolder = "screenshots"

func main() {
	fmt.Print("Enter the CSV or Excel file name: ")
	var inputFile string
	fmt.Scanln(&inputFile)

	// Create output folder if not exists
	if err := os.MkdirAll(outputFolder, os.ModePerm); err != nil {
		fmt.Println("[ERROR] Could not create output folder:", err)
		return
	}

	// Read input file
	entries, err := readFile(inputFile)
	if err != nil {
		fmt.Println("[ERROR]", err)
		return
	}

	// Iterate over entries and capture screenshots
	for _, entry := range entries {
		urls := generateURLs(entry.IP, entry.Port)
		for _, url := range urls {
			filename := filepath.Join(outputFolder, fmt.Sprintf("%s_%s_%s.png", url.Protocol, entry.IP, entry.Port))
			takeScreenshot(url.Address, filename)
		}
	}

	fmt.Println("[OK] Finished capturing screenshots.")
}

type entry struct {
	IP   string
	Port string
}

type urlData struct {
	Address  string
	Protocol string
}

func readFile(filename string) ([]entry, error) {
	var entries []entry

	if strings.HasSuffix(filename, ".csv") {
		file, err := os.Open(filename)
		if err != nil {
			return nil, err
		}
		defer file.Close()
		reader := csv.NewReader(file)
		records, err := reader.ReadAll()
		if err != nil {
			return nil, err
		}
		for _, record := range records[1:] { // Skip header
			entries = append(entries, entry{IP: record[0], Port: record[1]})
		}
	} else {
		xlFile, err := excelize.OpenFile(filename)
		if err != nil {
			return nil, err
		}
		sheetName := xlFile.GetSheetName(0)
		rows, err := xlFile.GetRows(sheetName)
		if err != nil {
			return nil, err
		}
		for _, row := range rows[1:] { // Skip header
			entries = append(entries, entry{IP: row[0], Port: row[1]})
		}
	}

	return entries, nil
}

func generateURLs(ip, port string) []urlData {
	var urls []urlData
	if port == "80" {
		urls = append(urls, urlData{fmt.Sprintf("http://%s:%s", ip, port), "http"})
	} else if port == "443" {
		urls = append(urls, urlData{fmt.Sprintf("https://%s:%s", ip, port), "https"})
	} else {
		urls = append(urls, urlData{fmt.Sprintf("http://%s:%s", ip, port), "http"})
		urls = append(urls, urlData{fmt.Sprintf("https://%s:%s", ip, port), "https"})
	}
	return urls
}

func takeScreenshot(urlStr, filename string) {
	fmt.Println("Trying:", urlStr)

	// Create a new ChromeDP context for each screenshot
	ctx, cancel := chromedp.NewContext(context.Background())
	defer cancel()

	// Set timeout for page load
	ctx, cancel = context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	var finalURL string
	var buf []byte
	err := chromedp.Run(ctx,
		chromedp.EmulateViewport(1920, 1080),
		chromedp.Navigate(urlStr),
		chromedp.Sleep(2*time.Second), // Allow page to load
		chromedp.Location(&finalURL),
		chromedp.CaptureScreenshot(&buf),
	)

	if err != nil {
		fmt.Println("[ERROR] Could not capture:", urlStr, err)
		return
	}

	parsedOriginal, _ := url.Parse(urlStr)
	parsedFinal, _ := url.Parse(finalURL)

	if parsedOriginal.Host != parsedFinal.Host || parsedOriginal.Scheme != parsedFinal.Scheme {
		fmt.Printf("[REDIRECTED] %s -> %s\n", urlStr, finalURL)
		filename = strings.Replace(filename, ".png", "_redirected.png", 1)
	}

	if parsedFinal.Scheme == "https" {
		fmt.Printf("[ENCRYPTED] %s\n", finalURL)
	} else {
		fmt.Printf("[UNENCRYPTED] %s\n", finalURL)
	}

	if err := os.WriteFile(filename, buf, 0644); err != nil {
		fmt.Println("[ERROR] Could not save screenshot:", err)
		return
	}

	fmt.Println("[OK] Screenshot saved:", filename)
}
