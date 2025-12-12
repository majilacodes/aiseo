"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface SERPResult {
  rank: number
  url: string
  title: string
  snippet: string
}

interface SERPAnalysis {
  primary_keyword: string
  secondary_keywords: string[]
  topics: string[]
  faqs: string[]
}

interface OutlineSection {
  heading_level: number
  heading: string
  slug: string
  summary: string
}

interface Outline {
  title: string
  sections: OutlineSection[]
}

interface Article {
  h1: string
  body_markdown: string
  seo: {
    title_tag: string
    meta_description: string
    primary_keyword: string
    secondary_keywords: string[]
    word_count_target: number
    estimated_word_count?: number
  }
  internal_links: Array<{
    anchor_text: string
    target_slug: string
  }>
  external_references: Array<{
    title: string
    url: string
    context_reason: string
  }>
}

interface JobResponse {
  id: string
  status: string
  error?: string
  serp_results?: SERPResult[]
  serp_analysis?: SERPAnalysis
  outline?: Outline
  article?: Article
}

export default function Home() {
  const [topic, setTopic] = useState("")
  const [wordCount, setWordCount] = useState(1500)
  const [language, setLanguage] = useState("en")
  const [loading, setLoading] = useState(false)
  const [jobData, setJobData] = useState<JobResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setJobData(null)

    try {
      const response = await fetch("/api/v1/jobs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic,
          target_word_count: wordCount,
          language,
        }),
      })

      const contentType = response.headers.get("content-type")
      if (!contentType || !contentType.includes("application/json")) {
        const text = await response.text()
        setError(`Server returned non-JSON response: ${text.substring(0, 200)}`)
        return
      }

      const data: JobResponse = await response.json()

      if (!response.ok) {
        setError(data.error || "Failed to create job")
        return
      }

      setJobData(data)
    } catch (err) {
      if (err instanceof TypeError && err.message.includes("fetch")) {
        setError("Unable to connect to the backend server. Please make sure the backend is running on http://localhost:8000")
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError("Request failed. Please check if the backend server is running.")
      }
    } finally {
      setLoading(false)
    }
  }

  const hasResults = jobData && (
    jobData.serp_results ||
    jobData.serp_analysis ||
    jobData.outline ||
    jobData.article
  )

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 text-center">SEO Engine</h1>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Create Job</CardTitle>
            <CardDescription>Enter the topic and parameters for your SEO article</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="topic">Topic</Label>
                <Textarea
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., best productivity tools for remote teams"
                  required
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="wordCount">Target Word Count</Label>
                  <Input
                    id="wordCount"
                    type="number"
                    min="300"
                    value={wordCount}
                    onChange={(e) => setWordCount(Number(e.target.value))}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select
                    id="language"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    <option value="en">English (en)</option>
                  </Select>
                </div>
              </div>

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "Creating Job..." : "Create Job"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {error && (
          <Card className="mb-6 border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">Error: {error}</p>
            </CardContent>
          </Card>
        )}

        {jobData && (
          <Card>
            <CardHeader>
              <CardTitle>Job Result</CardTitle>
              <CardDescription>
                Status: {jobData.status} {jobData.id && `• ID: ${jobData.id}`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {jobData.error && (
                <p className="text-destructive mb-4">Error: {jobData.error}</p>
              )}

              {hasResults && (() => {
                const availableTabs = [
                  jobData.serp_results && { value: "serp", label: "SERP Agent" },
                  jobData.serp_analysis && { value: "analysis", label: "SERP Analysis" },
                  jobData.outline && { value: "outline", label: "Outline" },
                  jobData.article && { value: "article", label: "Article" },
                ].filter(Boolean) as Array<{ value: string; label: string }>

                const defaultTab = availableTabs[0]?.value || "serp"
                const gridCols = availableTabs.length === 1 ? "grid-cols-1" :
                                 availableTabs.length === 2 ? "grid-cols-2" :
                                 availableTabs.length === 3 ? "grid-cols-3" : "grid-cols-4"

                return (
                  <Tabs defaultValue={defaultTab} className="w-full">
                    <TabsList className={`grid w-full ${gridCols}`}>
                      {availableTabs.map((tab) => (
                        <TabsTrigger key={tab.value} value={tab.value}>
                          {tab.label}
                        </TabsTrigger>
                      ))}
                    </TabsList>

                  {jobData.serp_results && (
                    <TabsContent value="serp" className="mt-4">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">SERP Results</h3>
                        {jobData.serp_results.length === 0 ? (
                          <p className="text-muted-foreground">No SERP results available.</p>
                        ) : (
                          <ul className="space-y-4">
                            {jobData.serp_results.map((result) => (
                              <li key={result.rank} className="border-b border-border pb-4">
                                <div className="flex items-start gap-2">
                                  <span className="font-semibold text-sm">Rank {result.rank}:</span>
                                  <div className="flex-1">
                                    <a
                                      href={result.url}
            target="_blank"
            rel="noopener noreferrer"
                                      className="text-primary hover:underline font-medium"
                                    >
                                      {result.title}
                                    </a>
                                    <p className="text-sm text-muted-foreground mt-1">
                                      {result.snippet}
                                    </p>
                                  </div>
                                </div>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </TabsContent>
                  )}

                  {jobData.serp_analysis && (
                    <TabsContent value="analysis" className="mt-4">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">SERP Analysis</h3>
                        <div className="space-y-3">
                          <div>
                            <span className="font-semibold">Primary Keyword: </span>
                            <span>{jobData.serp_analysis.primary_keyword || "N/A"}</span>
                          </div>

                          {jobData.serp_analysis.secondary_keywords &&
                            jobData.serp_analysis.secondary_keywords.length > 0 && (
                              <div>
                                <span className="font-semibold">Secondary Keywords: </span>
                                <span>{jobData.serp_analysis.secondary_keywords.join(", ")}</span>
                              </div>
                            )}

                          {jobData.serp_analysis.topics &&
                            jobData.serp_analysis.topics.length > 0 && (
                              <div>
                                <span className="font-semibold">Topics:</span>
                                <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
                                  {jobData.serp_analysis.topics.map((topic, idx) => (
                                    <li key={idx} className="text-sm">
                                      {topic}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                          {jobData.serp_analysis.faqs &&
                            jobData.serp_analysis.faqs.length > 0 && (
                              <div>
                                <span className="font-semibold">FAQs:</span>
                                <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
                                  {jobData.serp_analysis.faqs.map((faq, idx) => (
                                    <li key={idx} className="text-sm">
                                      {faq}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                        </div>
                      </div>
                    </TabsContent>
                  )}

                  {jobData.outline && (
                    <TabsContent value="outline" className="mt-4">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Outline</h3>
                        <div className="space-y-3">
                          <div>
                            <span className="font-semibold">Title (H1): </span>
                            <span>{jobData.outline.title || "N/A"}</span>
                          </div>

                          {jobData.outline.sections &&
                            jobData.outline.sections.length > 0 && (
                              <div>
                                <span className="font-semibold">Sections:</span>
                                <ul className="space-y-3 mt-2">
                                  {jobData.outline.sections.map((section, idx) => (
                                    <li key={idx} className="border-b border-border pb-3">
                                      <div className="space-y-1">
                                        <div>
                                          <span className="font-semibold">
                                            H{section.heading_level}:
                                          </span>{" "}
                                          <span>{section.heading}</span>
                                          <span className="text-muted-foreground text-sm ml-2">
                                            (slug: {section.slug})
                                          </span>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                          {section.summary}
                                        </p>
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                        </div>
                      </div>
                    </TabsContent>
                  )}

                  {jobData.article && (
                    <TabsContent value="article" className="mt-4">
                      <div className="space-y-6">
                        <div>
                          <h3 className="text-lg font-semibold mb-2">Article H1</h3>
                          <p>{jobData.article.h1 || "N/A"}</p>
                        </div>

                        <div>
                          <h3 className="text-lg font-semibold mb-2">Body</h3>
                          <div className="prose prose-invert max-w-none border border-border rounded-md p-4 bg-muted/20">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {jobData.article.body_markdown || ""}
                            </ReactMarkdown>
                          </div>
                        </div>

                        <div>
                          <h3 className="text-lg font-semibold mb-2">SEO</h3>
                          <div className="bg-muted/20 border border-border rounded-md p-4">
                            <pre className="text-sm font-mono whitespace-pre-wrap">
                              {JSON.stringify(jobData.article.seo, null, 2)}
                            </pre>
                          </div>
                        </div>

                        <div>
                          <h3 className="text-lg font-semibold mb-2">Internal Links</h3>
                          {jobData.article.internal_links &&
                          jobData.article.internal_links.length > 0 ? (
                            <ul className="list-disc list-inside space-y-1 ml-4">
                              {jobData.article.internal_links.map((link, idx) => (
                                <li key={idx} className="text-sm">
                                  {link.anchor_text} → {link.target_slug}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-muted-foreground text-sm">None</p>
                          )}
                        </div>

                        <div>
                          <h3 className="text-lg font-semibold mb-2">External References</h3>
                          {jobData.article.external_references &&
                          jobData.article.external_references.length > 0 ? (
                            <ul className="space-y-2">
                              {jobData.article.external_references.map((ref, idx) => (
                                <li key={idx} className="text-sm">
                                  <a
                                    href={ref.url}
            target="_blank"
            rel="noopener noreferrer"
                                    className="text-primary hover:underline"
                                  >
                                    {ref.title}
                                  </a>
                                  <span className="text-muted-foreground ml-2">
                                    — {ref.context_reason}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-muted-foreground text-sm">None</p>
                          )}
                        </div>
                      </div>
                    </TabsContent>
                  )}
                  </Tabs>
                )
              })()}

              {!hasResults && !jobData.error && (
                <p className="text-muted-foreground">No results available yet.</p>
              )}
            </CardContent>
          </Card>
        )}
        </div>
    </div>
  )
}
