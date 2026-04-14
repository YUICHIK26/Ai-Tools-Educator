import json
import os
import re
import random
import requests
from datetime import datetime
from groq import Groq
from dotenv import dotenv_values
from googlesearch import search  # Added for Rule [4]

# FIXED TUTORIAL TOOLS - All AI tools with recorded tutorial videos
# NOTE: This list is treated as "fixed" (never filtered as outdated) because we have tutorial videos for them.
FIXED_TUTORIAL_TOOLS = [
    # 1-10 (Original)
    {
        "name": "ChatGPT",
        "pricing": "Freemium",
        "category": "AI Writing Generation",
        "description": "Advanced AI writing assistant for various content types, blogs, emails, and creative writing",
        "steps": ["Visit chat.openai.com", "Create account", "Type your prompt", "Refine output as needed"],
        "video_tutorial": "1. AI Writing Generation/ChatGPT - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free tier with GPT-3.5, paid for GPT-4",
        "ranking": 9.5,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "IntercomFin",
        "pricing": "Paid",
        "category": "AI Chatbots",
        "description": "AI-powered customer support chatbot for businesses with advanced automation",
        "steps": ["Sign up at intercom.com", "Configure chatbot settings", "Train on your data", "Deploy to website"],
        "video_tutorial": "2. AI Chatbots/IntercomFin - Paid.mp4",
        "youtube_links": [],
        "free_limits": "14-day free trial",
        "ranking": 8.7,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Tensor.Art",
        "pricing": "Freemium",
        "category": "AI Image Generation",
        "description": "AI image generation tool with multiple models and styles for creative artwork",
        "steps": ["Visit tensor.art", "Create account", "Choose model", "Enter prompt", "Generate image"],
        "video_tutorial": "3. AI Image Generation/Tensor.Art - Free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free credits daily",
        "ranking": 9.0,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "BlackBox AI",
        "pricing": "Paid",
        "category": "AI Coding Assistant",
        "description": "AI coding assistant for developers with code completion and debugging features",
        "steps": ["Install extension", "Sign in", "Start coding", "Use AI suggestions"],
        "video_tutorial": "4. AI Coding Assistant/BlackBox Ai - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free tier available",
        "ranking": 8.8,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "Otter.ai",
        "pricing": "Paid",
        "category": "AI Transcription",
        "description": "AI-powered transcription service for meetings, interviews, and lectures with real-time captions",
        "steps": ["Sign up at otter.ai", "Record or upload audio", "Get instant transcription", "Edit and share"],
        "video_tutorial": "5. AI Transcription/Otter.ai - Paid.mp4",
        "youtube_links": [],
        "free_limits": "600 minutes free per month",
        "ranking": 9.1,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "ShortWave",
        "pricing": "Freemium",
        "category": "AI Email Assistant",
        "description": "AI email assistant that helps manage inbox, compose emails, and schedule messages",
        "steps": ["Sign up at shortwave.com", "Connect email", "Use AI features", "Manage smartly"],
        "video_tutorial": "6. AI Email Assistant/ShortWave - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free tier with basic features",
        "ranking": 8.5,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "Hailuo AI",
        "pricing": "Freemium",
        "category": "AI Video Generation",
        "description": "AI video generation tool for creating professional videos from text prompts",
        "steps": ["Visit hailuo.ai", "Enter video prompt", "Select style", "Generate video"],
        "video_tutorial": "7. AI Video Generation/Hailuo AI - Free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free video generations",
        "ranking": 8.9,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "Gamma AI",
        "pricing": "Freemium",
        "category": "AI Presentation Maker",
        "description": "AI presentation maker that creates professional slides from text input",
        "steps": ["Sign up at gamma.app", "Enter topic", "Choose template", "Generate presentation"],
        "video_tutorial": "8. AI Presentation Maker/Gamma AI - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free tier with watermark",
        "ranking": 9.2,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Grammarly",
        "pricing": "Paid",
        "category": "AI Grammar And Proofreading",
        "description": "AI-powered grammar checker and writing enhancement tool for error-free content",
        "steps": ["Install extension", "Create account", "Write content", "Review suggestions"],
        "video_tutorial": "9. AI Grammar And Proofreading/Grammarly - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Basic grammar checking free",
        "ranking": 9.4,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "Semrush",
        "pricing": "Paid",
        "category": "AI SEO Tools",
        "description": "Comprehensive SEO toolkit with AI-powered keyword research and content optimization",
        "steps": ["Sign up at semrush.com", "Enter domain", "Run SEO audit", "Implement suggestions"],
        "video_tutorial": "10. AI SEO Tools/Semrush - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free searches",
        "ranking": 9.3,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    # 11-20
    {
        "name": "Buffer",
        "pricing": "Freemium",
        "category": "AI Social Media Management",
        "description": "AI-powered social media scheduling and analytics tool for managing multiple platforms",
        "steps": ["Sign up at buffer.com", "Connect social accounts", "Schedule posts", "Analyze performance"],
        "video_tutorial": "11. AI Social Media Management/Buffer - Free.mp4",
        "youtube_links": [],
        "free_limits": "3 social channels free",
        "ranking": 8.6,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "Undetectable.ai",
        "pricing": "Paid",
        "category": "AI Paraphrasing Tools",
        "description": "AI paraphrasing tool that rewrites content to bypass AI detection systems",
        "steps": ["Visit undetectable.ai", "Paste text", "Select rewrite mode", "Generate human-like content"],
        "video_tutorial": "12. AI Paraphrasing Tools/Undetectable.ai - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free words",
        "ranking": 8.3,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "NaturalReader",
        "pricing": "Freemium",
        "category": "AI Voice Generation",
        "description": "AI text-to-speech tool with natural-sounding voices for audio content creation",
        "steps": ["Visit naturalreaders.com", "Paste or upload text", "Select voice", "Generate audio"],
        "video_tutorial": "13. AI Voice Generation/NaturalReader - Free.mp4",
        "youtube_links": [],
        "free_limits": "20 minutes free daily",
        "ranking": 8.7,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "10Web",
        "pricing": "Paid",
        "category": "AI Website Builders",
        "description": "AI website builder that creates WordPress sites automatically from business descriptions",
        "steps": ["Sign up at 10web.io", "Answer business questions", "Let AI build site", "Customize design"],
        "video_tutorial": "14. AI Website Builders/10Web - Paid.mp4",
        "youtube_links": [],
        "free_limits": "7-day free trial",
        "ranking": 8.9,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "Resoomer",
        "pricing": "Freemium",
        "category": "AI Summarization Tools",
        "description": "AI summarization tool that condenses long articles and documents into key points",
        "steps": ["Visit resoomer.com", "Paste text or upload file", "Click summarize", "Review summary"],
        "video_tutorial": "15. AI Summarization Tools/Resoomer - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free with character limits",
        "ranking": 8.4,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "Anyword",
        "pricing": "Paid",
        "category": "AI Copywriting",
        "description": "AI copywriting tool optimized for marketing content with predictive performance scores",
        "steps": ["Sign up at anyword.com", "Select content type", "Input brief", "Generate copy"],
        "video_tutorial": "16. AI Copywriting/Anyword - Paid.mp4",
        "youtube_links": [],
        "free_limits": "7-day free trial",
        "ranking": 8.8,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "Adobe Express",
        "pricing": "Freemium",
        "category": "AI Background Removal",
        "description": "AI-powered background removal tool integrated into Adobe's design platform",
        "steps": ["Visit adobe.com/express", "Upload image", "Click remove background", "Download result"],
        "video_tutorial": "17. AI Background Removal/Adobe Express - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free tier available",
        "ranking": 9.0,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "Udio",
        "pricing": "Paid",
        "category": "AI Music Generation",
        "description": "AI music generation tool that creates original songs from text descriptions",
        "steps": ["Sign up at udio.com", "Describe music style", "Generate track", "Download audio"],
        "video_tutorial": "18. AI Music Generation/Udio - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free generations",
        "ranking": 8.9,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Magic Studio",
        "pricing": "Freemium",
        "category": "AI Photo Editing",
        "description": "AI photo editing tool with automatic enhancements and creative filters",
        "steps": ["Visit magicstudio.com", "Upload photo", "Apply AI edits", "Download enhanced image"],
        "video_tutorial": "19. AI Photo Editing/Magic Studio - Free.mp4",
        "youtube_links": [],
        "free_limits": "10 free edits per month",
        "ranking": 8.5,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "Avoma",
        "pricing": "Paid",
        "category": "AI Meeting Assistants",
        "description": "AI meeting assistant that records, transcribes, and summarizes meetings automatically",
        "steps": ["Sign up at avoma.com", "Connect calendar", "Join meeting", "Review AI notes"],
        "video_tutorial": "20. AI Meeting Assistants/Avoma - Paid.mp4",
        "youtube_links": [],
        "free_limits": "14-day free trial",
        "ranking": 8.7,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    # 21-30
    {
        "name": "Tableau AI",
        "pricing": "Paid",
        "category": "AI Data Analysis",
        "description": "AI-powered data visualization and analytics platform for business intelligence",
        "steps": ["Sign up at tableau.com", "Connect data source", "Use AI insights", "Create dashboards"],
        "video_tutorial": "21. AI Data Analysis/Tableau AI - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Free trial available",
        "ranking": 9.1,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "Tableau.ai",
        "pricing": "Paid",
        "category": "AI Data Analysis",
        "description": "AI-powered analytics and visualization tool (tutorial available in your library).",
        "steps": ["Sign up at tableau.com", "Connect data source", "Use AI insights", "Build dashboards"],
        "video_tutorial": "21. AI Data Analysis/Tableau.ai - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Free trial available",
        "ranking": 9.1,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "Google Translate",
        "pricing": "Free",
        "category": "AI Translation",
        "description": "AI translation service supporting 100+ languages with text, speech, and image translation",
        "steps": ["Visit translate.google.com", "Select languages", "Enter text", "Get translation"],
        "video_tutorial": "22. AI Translation/Google Translate - Free.mp4",
        "youtube_links": [],
        "free_limits": "Completely free",
        "ranking": 9.5,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "Reclaim.ai",
        "pricing": "Paid",
        "category": "AI Personal Assistant",
        "description": "AI personal assistant for smart calendar management and task prioritization",
        "steps": ["Sign up at reclaim.ai", "Connect calendar", "Set preferences", "Let AI schedule"],
        "video_tutorial": "23. AI Personal Assistant/Reclaim.ai - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Free tier available",
        "ranking": 8.6,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Freshteam",
        "pricing": "Freemium",
        "category": "AI Resume Screening",
        "description": "AI resume screening tool that automatically ranks candidates based on job requirements",
        "steps": ["Sign up at freshteam.com", "Post job", "Upload resumes", "Review AI rankings"],
        "video_tutorial": "24. AI Resume Screening/Freshteam - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free for up to 50 employees",
        "ranking": 8.4,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "Originality.ai",
        "pricing": "Paid",
        "category": "AI Plagiarism Checkers",
        "description": "AI plagiarism detection tool specialized in detecting AI-generated content",
        "steps": ["Visit originality.ai", "Paste content", "Run scan", "Review plagiarism report"],
        "video_tutorial": "25. AI Plagiarism Checkrs/Originality.ai - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Pay per scan",
        "ranking": 8.8,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "DesignEvo",
        "pricing": "Freemium",
        "category": "AI Logo Design",
        "description": "AI logo design tool with thousands of templates and customization options",
        "steps": ["Visit designevo.com", "Choose template", "Customize design", "Download logo"],
        "video_tutorial": "26. AI Logo Design/DesignEvo - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free with low resolution",
        "ranking": 8.3,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "Interior AI",
        "pricing": "Paid",
        "category": "AI Interior Design",
        "description": "AI interior design tool that generates room designs from photos or descriptions",
        "steps": ["Visit interiorai.com", "Upload room photo", "Select style", "Generate designs"],
        "video_tutorial": "27. AI Interior Design/Interior AI - Paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free renders",
        "ranking": 8.7,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "Bitrix24",
        "pricing": "Freemium",
        "category": "AI HR Assistants",
        "description": "AI HR management platform with recruitment, onboarding, and employee management features",
        "steps": ["Sign up at bitrix24.com", "Set up company", "Configure HR modules", "Use AI features"],
        "video_tutorial": "28. AI HR Assistants/Bitrix24 - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free for unlimited users",
        "ranking": 8.5,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "Gorgias",
        "pricing": "Paid",
        "category": "AI Customer Support",
        "description": "AI customer support platform for e-commerce with automated responses and ticket management",
        "steps": ["Sign up at gorgias.com", "Connect store", "Set up automations", "Handle tickets"],
        "video_tutorial": "29. AI Customer Support/Gorgias - Paid.mp4",
        "youtube_links": [],
        "free_limits": "7-day free trial",
        "ranking": 8.9,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "RubberDuck",
        "pricing": "Freemium",
        "category": "AI Code Debugging",
        "description": "AI code debugging assistant that explains errors and suggests fixes in real-time",
        "steps": ["Install extension", "Write code", "Get AI debugging help", "Fix errors"],
        "video_tutorial": "30. AI Code Debugging/RubberDuck - Free.mp4",
        "youtube_links": [],
        "free_limits": "Free tier available",
        "ranking": 8.6,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    # 31-40
    {
        "name": "Uizard",
        "pricing": "Paid",
        "category": "AI UX-UI Design",
        "description": "AI UX/UI design tool that converts sketches and wireframes into professional designs",
        "steps": ["Sign up at uizard.io", "Upload sketch or describe UI", "Generate design", "Customize"],
        "video_tutorial": "31. AI UX-UI Design/31 Uizard - paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free projects",
        "ranking": 8.7,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "D-ID",
        "pricing": "Paid",
        "category": "AI Avatar Creation",
        "description": "AI avatar creation tool for generating talking head videos from photos and text",
        "steps": ["Visit d-id.com", "Upload photo", "Enter script", "Generate talking avatar"],
        "video_tutorial": "32. AI Avatar Creation/32 D-ID - paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free credits",
        "ranking": 8.8,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "Outreach.io",
        "pricing": "Paid",
        "category": "AI Sales Outreach",
        "description": "AI sales engagement platform for automating outreach and managing sales workflows",
        "steps": ["Sign up at outreach.io", "Import contacts", "Create sequences", "Track engagement"],
        "video_tutorial": "33. AI Sales Outreach/33 Outreach.io - paid.mp4",
        "youtube_links": [],
        "free_limits": "Custom pricing only",
        "ranking": 9.0,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "Google Trends",
        "pricing": "Free",
        "category": "AI Market Research",
        "description": "AI-powered market research tool showing search trends and consumer interest patterns",
        "steps": ["Visit trends.google.com", "Enter search terms", "Compare trends", "Analyze data"],
        "video_tutorial": "34. AI Market Research/34 Google Trends - free.mp4",
        "youtube_links": [],
        "free_limits": "Completely free",
        "ranking": 9.2,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "LinkedIn Recruiter",
        "pricing": "Paid",
        "category": "AI Recruiting",
        "description": "AI recruiting platform with advanced candidate search and recommendation features",
        "steps": ["Sign up for recruiter", "Define criteria", "Search candidates", "Use AI recommendations"],
        "video_tutorial": "35. AI Recruiting/35 LinkedIn Recruiter - paid.mp4",
        "youtube_links": [],
        "free_limits": "Premium subscription required",
        "ranking": 9.1,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "NewArc.ai",
        "pricing": "Freemium",
        "category": "AI Fashion Design",
        "description": "AI fashion design tool for creating clothing designs and patterns automatically",
        "steps": ["Visit newarc.ai", "Describe design", "Generate patterns", "Download designs"],
        "video_tutorial": "36. AI Fashion Design/36 NewArc.ai - free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free designs",
        "ranking": 8.4,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "Speeko",
        "pricing": "Paid",
        "category": "AI Speechwriting",
        "description": "AI speechwriting and public speaking coach with real-time feedback on delivery",
        "steps": ["Download Speeko app", "Practice speech", "Get AI feedback", "Improve delivery"],
        "video_tutorial": "37. AI Speechwriting/37 Speeko - paid.mp4",
        "youtube_links": [],
        "free_limits": "7-day free trial",
        "ranking": 8.5,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "Podium",
        "pricing": "Freemium",
        "category": "AI Podcast Show Notes",
        "description": "AI tool for generating podcast show notes, transcripts, and episode summaries",
        "steps": ["Visit podium.page", "Upload podcast", "Generate show notes", "Export content"],
        "video_tutorial": "38. AI Podcast Show Notes/38 Podium - free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free episodes",
        "ranking": 8.3,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "1Password",
        "pricing": "Paid",
        "category": "AI Password Management",
        "description": "AI-enhanced password manager with breach monitoring and secure password generation",
        "steps": ["Download 1Password", "Create vault", "Save passwords", "Use autofill"],
        "video_tutorial": "39. AI Password Management/39 1Password - paid.mp4",
        "youtube_links": [],
        "free_limits": "14-day free trial",
        "ranking": 9.0,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "Wonderplan",
        "pricing": "Freemium",
        "category": "AI Travel Planning",
        "description": "AI travel planning assistant that creates personalized itineraries based on preferences",
        "steps": ["Visit wonderplan.ai", "Enter destination", "Set preferences", "Get itinerary"],
        "video_tutorial": "40. AI Travel Planning/40 Wonderplan - free.mp4",
        "youtube_links": [],
        "free_limits": "Free basic plans",
        "ranking": 8.6,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    # 41-50
    {
        "name": "XMind AI",
        "pricing": "Paid",
        "category": "AI Mind Mapping",
        "description": "AI mind mapping tool that automatically organizes ideas and creates visual concept maps",
        "steps": ["Download XMind", "Create map", "Use AI suggestions", "Export diagram"],
        "video_tutorial": "41. AI Mind Mapping/41 XMind AI - paid.mp4",
        "youtube_links": [],
        "free_limits": "Basic version free",
        "ranking": 8.7,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Instrumentl",
        "pricing": "Paid",
        "category": "AI Grant Writing",
        "description": "AI grant writing platform that helps find funding opportunities and write proposals",
        "steps": ["Sign up at instrumentl.com", "Search grants", "Use AI writer", "Submit proposals"],
        "video_tutorial": "42. AI Grant Writing/42 Instrumentl - paid.mp4",
        "youtube_links": [],
        "free_limits": "14-day free trial",
        "ranking": 8.8,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "Amto AI",
        "pricing": "Freemium",
        "category": "AI Legal Document Review",
        "description": "AI legal document review tool for contract analysis and risk assessment",
        "steps": ["Visit amto.ai", "Upload contract", "Run AI analysis", "Review findings"],
        "video_tutorial": "43. AI Legal Document Review/43 Amto AI - free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free reviews",
        "ranking": 8.5,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "Zoho Expense",
        "pricing": "Freemium",
        "category": "AI Expense Management",
        "description": "AI expense management system with automatic receipt scanning and categorization",
        "steps": ["Sign up at zoho.com/expense", "Scan receipts", "Track expenses", "Generate reports"],
        "video_tutorial": "44. AI Expense Management/44 Zoho Expense - free.mp4",
        "youtube_links": [],
        "free_limits": "Free for 3 users",
        "ranking": 8.6,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "FitBod",
        "pricing": "Paid",
        "category": "AI Fitness Trainers",
        "description": "AI fitness trainer app that creates personalized workout plans based on goals and equipment",
        "steps": ["Download FitBod app", "Set fitness goals", "Get AI workout", "Track progress"],
        "video_tutorial": "45. AI Fitness Trainers/45 FitBod - paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free workouts",
        "ranking": 8.9,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "Cronometer",
        "pricing": "Freemium",
        "category": "AI Meal Planning",
        "description": "AI meal planning and nutrition tracking app with personalized recommendations",
        "steps": ["Download Cronometer", "Set diet goals", "Log meals", "Get AI suggestions"],
        "video_tutorial": "46. AI Meal Planning/46 Cronometer - free.mp4",
        "youtube_links": [],
        "free_limits": "Free basic tracking",
        "ranking": 8.4,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "Monarch Money",
        "pricing": "Paid",
        "category": "AI Financial Advising",
        "description": "AI financial advisor for budgeting, investment tracking, and financial planning",
        "steps": ["Sign up at monarchmoney.com", "Link accounts", "Set financial goals", "Get AI advice"],
        "video_tutorial": "47. AI Financial Advising/47 Monarch Money - paid.mp4",
        "youtube_links": [],
        "free_limits": "7-day free trial",
        "ranking": 8.8,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Memrise",
        "pricing": "Freemium",
        "category": "AI Language Learning",
        "description": "AI language learning app with personalized lessons and spaced repetition",
        "steps": ["Download Memrise", "Choose language", "Start lessons", "Practice daily"],
        "video_tutorial": "48. AI Language Learning/48 Memrise - free.mp4",
        "youtube_links": [],
        "free_limits": "Free courses available",
        "ranking": 8.7,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "Monday.com",
        "pricing": "Paid",
        "category": "AI Project Management",
        "description": "AI project management platform with automation, tracking, and team collaboration features",
        "steps": ["Sign up at monday.com", "Create workspace", "Set up projects", "Use AI automations"],
        "video_tutorial": "49. AI Project Management_/49 Monday.com - paid.mp4",
        "youtube_links": [],
        "free_limits": "Free for 2 users",
        "ranking": 9.0,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "MonkeyLearn",
        "pricing": "Freemium",
        "category": "AI Sentiment Analysis",
        "description": "AI sentiment analysis tool for analyzing customer feedback and social media sentiment",
        "steps": ["Sign up at monkeylearn.com", "Upload data", "Run analysis", "Review insights"],
        "video_tutorial": "50. AI Sentiment Analysis_/50 MonkeyLearn - free.mp4",
        "youtube_links": [],
        "free_limits": "300 queries free per month",
        "ranking": 8.5,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    # 51-60
    {
        "name": "Respeecher",
        "pricing": "Paid",
        "category": "AI Voice Cloning",
        "description": "AI voice cloning technology for creating synthetic voices from audio samples",
        "steps": ["Visit respeecher.com", "Upload voice sample", "Train model", "Generate speech"],
        "video_tutorial": "51. AI Voice Cloning/51 Respeecher - paid.mp4",
        "youtube_links": [],
        "free_limits": "Custom enterprise pricing",
        "ranking": 8.9,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "OpusClip",
        "pricing": "Freemium",
        "category": "AI Video Editing",
        "description": "AI video editing tool that automatically creates short clips from long-form content",
        "steps": ["Visit opus.pro", "Upload video", "AI generates clips", "Download shorts"],
        "video_tutorial": "52. AI Video Editing_/52 OpusClip - free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free processing time",
        "ranking": 8.8,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "Appy Pie",
        "pricing": "Paid",
        "category": "AI App Development",
        "description": "No-code AI app builder for creating mobile and web applications without coding",
        "steps": ["Sign up at appypie.com", "Choose app type", "Use AI builder", "Publish app"],
        "video_tutorial": "53. AI Thumbnail Generation_/53 Appy Pie - paid.mp4",
        "youtube_links": [],
        "free_limits": "7-day free trial",
        "ranking": 8.4,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Consensus",
        "pricing": "Freemium",
        "category": "AI Academic Writing",
        "description": "AI academic research tool that summarizes scientific papers and extracts key findings",
        "steps": ["Visit consensus.app", "Enter research question", "Get AI summary", "Review papers"],
        "video_tutorial": "54. AI Academic Writing_/54 Consensus - free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free searches",
        "ranking": 8.9,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    },
    {
        "name": "Soundful",
        "pricing": "Paid",
        "category": "AI Songwriting",
        "description": "AI songwriting tool that generates royalty-free music tracks for content creators",
        "steps": ["Sign up at soundful.com", "Select genre", "Customize mood", "Generate track"],
        "video_tutorial": "55. AI Songwriting_/55 Soundful - paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free downloads",
        "ranking": 8.6,
        "last_verified": "2025-01-12",
        "has_tutorial_video": True
    },
    {
        "name": "Novel AI",
        "pricing": "Paid",
        "category": "AI Story Writing",
        "description": "AI story writing assistant specialized in creative fiction and narrative generation",
        "steps": ["Sign up at novelai.net", "Start story", "Use AI continuation", "Edit output"],
        "video_tutorial": "56. AI Story Writing_/56 Novel AI - paid.mp4",
        "youtube_links": [],
        "free_limits": "Limited free trial",
        "ranking": 8.7,
        "last_verified": "2025-01-11",
        "has_tutorial_video": True
    },
    {
        "name": "Adobe Color",
        "pricing": "Freemium",
        "category": "AI Brand Kit Generators",
        "description": "AI color palette generator for creating cohesive brand color schemes",
        "steps": ["Visit color.adobe.com", "Choose base color", "Generate palette", "Export codes"],
        "video_tutorial": "57. AI Brand Kit Generators_/57 Adobe color - free.mp4",
        "youtube_links": [],
        "free_limits": "Free with Adobe account",
        "ranking": 8.8,
        "last_verified": "2025-01-10",
        "has_tutorial_video": True
    },
    {
        "name": "GetProspect",
        "pricing": "Freemium",
        "category": "AI Lead Generation",
        "description": "AI lead generation tool for finding and verifying business email addresses",
        "steps": ["Sign up at getprospect.com", "Search for leads", "Verify emails", "Export contacts"],
        "video_tutorial": "58. AI Lead Generation_/58 GetProspect - free.mp4",
        "youtube_links": [],
        "free_limits": "50 free emails per month",
        "ranking": 8.5,
        "last_verified": "2025-01-15",
        "has_tutorial_video": True
    },
    {
        "name": "FingerprintJS",
        "pricing": "Freemium",
        "category": "AI Fraud Detection",
        "description": "AI fraud detection system using browser fingerprinting for user identification",
        "steps": ["Sign up at fingerprintjs.com", "Install SDK", "Configure rules", "Monitor activity"],
        "video_tutorial": "59. AI Fraud Detection/59 FingerprintJS - free.mp4",
        "youtube_links": [],
        "free_limits": "Limited free API calls",
        "ranking": 8.9,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Signifyd",
        "pricing": "Paid",
        "category": "AI Fraud Detection",
        "description": "AI fraud detection and chargeback protection platform for e-commerce businesses.",
        "steps": ["Sign up at signifyd.com", "Connect your store", "Configure fraud rules", "Monitor decisions"],
        "video_tutorial": "59. AI Fraud Detection/59 Signifyd - paid.mp4",
        "youtube_links": [],
        "free_limits": "Typically custom pricing / demo-based",
        "ranking": 8.8,
        "last_verified": "2025-01-14",
        "has_tutorial_video": True
    },
    {
        "name": "Acloset",
        "pricing": "Freemium",
        "category": "AI Personal Stylists",
        "description": "AI personal stylist app that creates outfit recommendations from your wardrobe",
        "steps": ["Download Acloset app", "Upload clothes", "Get AI outfit suggestions", "Save looks"],
        "video_tutorial": "60. AI Personal Stylists/60 Acloset - free.mp4",
        "youtube_links": [],
        "free_limits": "Free basic features",
        "ranking": 8.3,
        "last_verified": "2025-01-13",
        "has_tutorial_video": True
    }
]



class AIEducator:
    def __init__(self):
        env_vars = dotenv_values(".env")
        self.groq_api_key = env_vars.get("GroqAPIKey")
        self.client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.tools_data = self.load_tools_data()
        self.last_updated = None

    def load_tools_data(self):
        """Load AI tools database from JSON file"""
        tools_file = os.path.join('Data', 'ai_tools_database.json')
        if os.path.exists(tools_file):
            with open(tools_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.last_updated = data.get('last_updated')
                self._sync_fixed_tutorial_tools(data)
                return data
        else:
            return self.create_default_tools_data()

    def _normalize_tool_name(self, name: str) -> str:
        """Normalize tool names for matching (handles prefixes like '59 Signifyd')."""
        name = (name or '').strip().lower()
        name = re.sub(r'^\s*\d+\s*[\.\-_:]*\s*', '', name)
        return name

    def _sync_fixed_tutorial_tools(self, data):
        """Ensure all fixed tutorial tools are present in the database."""
        existing_tools = {}
        for category in data.get('categories', []):
            for tool in category.get('tools', []):
                existing_tools[self._normalize_tool_name(tool.get('name', ''))] = tool

        for tool_data in FIXED_TUTORIAL_TOOLS:
            key = self._normalize_tool_name(tool_data.get('name', ''))
            if key in existing_tools:
                existing_tools[key].update(tool_data)
            else:
                category_found = False
                for category in data.get('categories', []):
                    if category['name'] == tool_data['category']:
                        category['tools'].append(tool_data)
                        category_found = True
                        break
                if not category_found:
                    new_category = {
                        "id": len(data.get('categories', [])) + 1,
                        "name": tool_data['category'],
                        "description": f"Tools for {tool_data['category']}",
                        "tools": [tool_data]
                    }
                    data.setdefault('categories', []).append(new_category)

    def create_default_tools_data(self):
        """Create AI tools database from the 60 fixed tutorial tools"""
        default_data = {
            "last_updated": datetime.now().isoformat(),
            "categories": []
        }

        categories_dict = {}
        for tool in FIXED_TUTORIAL_TOOLS:
            cat_name = tool['category']
            if cat_name not in categories_dict:
                categories_dict[cat_name] = {
                    "id": len(categories_dict) + 1,
                    "name": cat_name,
                    "description": f"Tools for {cat_name}",
                    "tools": []
                }
            categories_dict[cat_name]['tools'].append(tool)

        default_data['categories'] = list(categories_dict.values())

        os.makedirs('Data', exist_ok=True)
        with open(os.path.join('Data', 'ai_tools_database.json'), 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2)

        return default_data

    def get_categories(self):
        """Return list of all AI tool category names"""
        return [cat["name"] for cat in self.tools_data["categories"]]

    def _dynamic_rank_score(self, tool: dict, is_fixed: bool) -> float:
        """Compute a dynamic score that prefers fresh tools and tutorial-available tools."""
        base = float(tool.get('ranking', 0) or 0)

        # Freshness boost for non-fixed tools only (fixed tools are allowed to be older)
        freshness_boost = 0.0
        if not is_fixed:
            try:
                last_verified = datetime.fromisoformat(tool.get('last_verified', '2024-01-01'))
                age_days = (datetime.now() - last_verified).days
                freshness_boost = max(0.0, (180.0 - float(age_days)) / 180.0) * 1.5
            except Exception:
                freshness_boost = 0.0

        tutorial_boost = 0.75 if tool.get('has_tutorial_video', False) else 0.0
        return base + freshness_boost + tutorial_boost

    def get_tools_by_category(self, category_name):
        """Return tools for a given category, fixed tools always included."""
        for category in self.tools_data["categories"]:
            if category["name"].lower() == category_name.lower():
                tools = category["tools"]
                current_date = datetime.now()
                recent_tools = []
                for tool in tools:
                    is_fixed = any(self._normalize_tool_name(ft['name']) == self._normalize_tool_name(tool.get('name', '')) for ft in FIXED_TUTORIAL_TOOLS)
                    if is_fixed:
                        recent_tools.append(tool)
                    else:
                        last_verified = datetime.fromisoformat(tool.get('last_verified', '2024-01-01'))
                        if (current_date - last_verified).days < 180:
                            recent_tools.append(tool)

                recent_tools.sort(
                    key=lambda x: self._dynamic_rank_score(
                        x,
                        any(self._normalize_tool_name(ft['name']) == self._normalize_tool_name(x.get('name', '')) for ft in FIXED_TUTORIAL_TOOLS)
                    ),
                    reverse=True
                )
                return recent_tools
        return []

    def search_tools(self, query):
        """
        Search tools by relevance to the query.

        Scoring:
          +15  exact full-query match against tool name
          +10  tool name contains the full query string
          +8   individual keyword found in tool name
          +6   individual keyword found in category name
          +3   individual keyword found in description
          +8   full query found in category name
          +5   full query found in description
          +3   tool has a tutorial video (tie-breaker)

        Final score = relevance_score + tool.ranking
        Fixed tutorial tools are never filtered by date.
        Dynamic tools older than 6 months are excluded.
        """
        results = []
        query_lower = query.lower()
        keywords = [k for k in query_lower.split() if len(k) > 2]  # ignore tiny words

        for category in self.tools_data["categories"]:
            for tool in category["tools"]:
                relevance_score = 0

                is_fixed = any(
                    self._normalize_tool_name(ft.get('name', '')) == self._normalize_tool_name(tool.get('name', ''))
                    for ft in FIXED_TUTORIAL_TOOLS
                )

                # Skip stale dynamic tools
                if not is_fixed:
                    try:
                        last_verified = datetime.fromisoformat(tool.get('last_verified', '2024-01-01'))
                    except Exception:
                        last_verified = datetime.fromisoformat('2024-01-01')

                    if (datetime.now() - last_verified).days >= 180:
                        continue

                tool_name_lower     = tool["name"].lower()
                category_name_lower = category["name"].lower()
                description_lower   = tool["description"].lower()

                # Full-query matches
                if query_lower == tool_name_lower:
                    relevance_score += 15
                elif query_lower in tool_name_lower:
                    relevance_score += 10

                if query_lower in category_name_lower:
                    relevance_score += 8

                if query_lower in description_lower:
                    relevance_score += 5

                # Per-keyword matches
                for kw in keywords:
                    if kw in tool_name_lower:
                        relevance_score += 8
                    if kw in category_name_lower:
                        relevance_score += 6
                    if kw in description_lower:
                        relevance_score += 3

                # Tutorial-video tie-breaker
                if tool.get('has_tutorial_video', False):
                    relevance_score += 3

                if relevance_score > 0:
                    final_score = relevance_score + self._dynamic_rank_score(tool, is_fixed)
                    results.append({
                        **tool,
                        "category": category["name"],
                        "relevance_score": final_score
                    })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results

    def _get_dynamic_search_data(self, query):
        """Fetch real-time data from Google for Rule [4]"""
        try:
            results = list(search(f"best AI tools for {query} 2025 features pricing", advanced=True, num_results=10))
            data = "Recent AI Tool Search Results:\n"
            for i in results:
                data += f"Title: {i.title}\nURL: {i.url}\nDescription: {i.description}\n\n"
            return data
        except Exception as e:
            print(f"[AIEducator] Dynamic search failed: {e}")
            return ""

    def process_ai_query(self, query):
        """Process query using AGENT Identity and Role 1 Rules"""
        print(f"[AIEducator] AGENT Role 1 Activation: {query}")
        
        # 1. Fetch Dynamic Data (Rule [4])
        dynamic_data = self._get_dynamic_search_data(query)
        
        # 2. Get 5 Relevant Tools from LLM using Dynamic Data
        try:
            prompt = f"""
ROLE: AI TOOLS EDUCATOR
TASK: Recommend exactly 5 current AI tools for: '{query}'
DATA SOURCE: 
{dynamic_data}

RULES:
1. Return exactly 5 tools formatted cleanly in standard Markdown (do NOT use ASCII boxes).
2. For each tool, follow this Markdown format precisely:

### 🛠️ **[Tool Name]**
* **🌐 URL:** [official link]
* **📌 Task Fit:** [one sentence]
* **💰 Pricing:**
  * Free: [limits]
  * Pro: $X/month
* **⚡ Key Features:**
  * [Feature 1]
  * [Feature 2]
* **🎯 Best For:** [target user type]
* **⚠️ Honest Cons:** [technical limitation]
* 🎬 **YOUTUBE_QUERY:** "[tool name] [specific use case] tutorial 2025 step by step"

3. After all 5 tools, provide a Markdown '📊 **COMPARISON TABLE**' with columns: | Tool | Free Tier | Paid From | Best Feature | Ease (1-5) | Best For |
4. End with '🏆 **AI TOOLS EDUCATOR RECOMMENDS:** *[DIRECT CHOICE]* - [REASON].'
5. IMPORTANT: If the user is asking for a real-world task (e.g., Aadhaar, PAN, Passport), recommend official or specialized utility tools, NEVER generic design tools like Adobe/Canva unless specifically useful for documentation parts.
"""
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.3
            )

            raw_response = completion.choices[0].message.content
            
            # 3. Extract YOUTUBE_QUERYs and fetch #1 results (Rule [5])
            yt_queries = re.findall(r'🎬  YOUTUBE_QUERY: "([^"]+)"', raw_response)
            yt_vids = []
            
            # Fetch tool-specific tutorials
            for yq in yt_queries[:5]:
                vid_data = self.search_youtube_dynamic(yq, limit=1)
                if vid_data: yt_vids.append(vid_data[0])
            
            # 4. CRITICAL: Fetch 20+ Direct Query Tutorials to meet user requirement
            direct_vids = self.search_youtube_dynamic(query, limit=20)
            
            # Merge and deduplicate
            seen_ids = {v['id'] for v in yt_vids}
            for dv in direct_vids:
                if dv['id'] not in seen_ids:
                    yt_vids.append(dv)
                    seen_ids.add(dv['id'])
            
            # 5. Standard AGENT Prefix
            final_response = f"⚡ AI TOOLS EDUCATOR: Identifying top 5 AI tools for your task + fetching 20+ hyper-relevant tutorials...\n\n{raw_response}"
            
            return self.format_response_with_tutorials(final_response, [], yt_vids[:30])

        except Exception as e:
            print(f"[AIEducator] AGENT Error: {e}")
            return "⚡ AI TOOLS EDUCATOR: I encountered an error. Scanning system components to fix...\n" + self.get_fallback_response(query)

    def get_fallback_response(self, query):
        """Fallback when Groq is unavailable — uses local search results"""
        relevant_tools = self.search_tools(query)

        if not relevant_tools:
            return (
                "I couldn't find AI tools matching your query. "
                "Try: AI Writing Tools, Image Generation, Video Tools, Coding Assistants."
            )

        top_tools = relevant_tools[:5]

        response = f"🔍 **AI Tools for '{query}'**\n\n"
        for i, tool in enumerate(top_tools, 1):
            response += f"**{i}. {tool['name']}** ({tool['category']})\n"
            response += f"   💰 **Pricing:** {tool['pricing']}\n"
            response += f"   📝 {tool['description']}\n"
            if tool.get('free_limits'):
                response += f"   🆓 **Free tier:** {tool['free_limits']}\n"
            if tool.get('has_tutorial_video'):
                response += f"   🎥 Tutorial video available\n"
            response += "\n"

        response += "\n💡 Ask me about specific tools or categories for more detail!"
    def generate_smart_queries(self, user_query):
        """Pass 1: Use LLM to generate targeted search strings and filters."""
        prompt = f"""
You are a YouTube search expert. The user asked: "{user_query}"

Return ONLY a JSON object with these exact keys:
{{
  "primary_query": "best 6-word YouTube search string to find this exact video",
  "backup_query": "alternative 6-word search if primary fails",
  "must_include": ["2-4 words that MUST appear in a relevant title"],
  "must_exclude": ["4-8 words that signal an OFF-TOPIC video for THIS specific query"],
  "intent_type": "one of: tutorial / explanation / news / review / comparison"
}}

Rules:
- must_exclude should be smart. If user wants 'new Aadhaar apply', exclude: ['update','dob','pvc','child','download','nri','supervisor','fake','illegal','scam','prank','generator','angry'].
- If the task is governmental or sensitive (Aadhaar, Bank, etc.), HEAVILY exclude anything related to 'fake', 'prank', or 'unofficial' content.
- Think about what ADJACENT but IRRELEVANT videos exist for this topic and exclude those.
- No explanation. JSON only.
"""
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"[YouTube Pipeline] Query generation failed: {e}")
            return {
                "primary_query": f"{user_query} tutorial 2025",
                "backup_query": f"{user_query} guide",
                "must_include": user_query.split()[:2],
                "must_exclude": [],
                "intent_type": "tutorial"
            }

    def rerank_titles(self, user_query, video_data, intent_type):
        """Pass 2: Batch score video titles using LLM."""
        if not video_data: return []
        
        numbered_titles = "\n".join([f"{i}. {v['name']}" for i, v in enumerate(video_data)])
        prompt = f"""
User's question: "{user_query}"
User wants: "{intent_type}" content

Below are YouTube video titles (numbered). Score each from 0-10:
- 10 = directly and completely answers the user's question
- 5  = loosely related, partially useful  
- 0  = completely off-topic or misleading

Be STRICT. Most titles should score 3 or below.

Titles:
{numbered_titles}

Return ONLY a JSON array of numbers. Example: [7, 2, 9, 0, 4, ...]
No explanation. Numbers only.
"""
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            # Find the JSON array in the text (sometimes LLMs wrap in backticks)
            content = completion.choices[0].message.content
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                scores = json.loads(match.group(0))
                for i, score in enumerate(scores):
                    if i < len(video_data):
                        video_data[i]["llm_score"] = float(score)
            return video_data
        except Exception as e:
            print(f"[YouTube Pipeline] Re-ranking failed: {e}")
            for v in video_data: v["llm_score"] = 5.0 # Neutral fallback
            return video_data

    def compute_final_score(self, vid, must_include, must_exclude):
        """Weighted scoring formula."""
        title = vid["name"].lower()
        llm_score = vid.get("llm_score", 0)
        
        # Hard disqualifiers
        if llm_score < 4: return -999
        for word in must_exclude:
            if word.lower() in title: return -999
            
        must_include_hits = sum(1 for word in must_include if word.lower() in title)
        
        # Reward formula
        relevance_weight = llm_score * 3.0
        keyword_bonus    = must_include_hits * 2.0
        
        # Recency boost (simple regex search for year)
        year_boost = 0
        if "2025" in title or "2026" in title: year_boost = 5
        elif "2024" in title: year_boost = 2
        
        return relevance_weight + keyword_bonus + year_boost

    def search_youtube_dynamic(self, query: str, limit: int = 40) -> list[dict]:
        """Hyper-relevance two-pass pipeline returning 20+ videos."""
        print(f"[YouTube Pipeline] Processing: {query}")
        smart_data = self.generate_smart_queries(query)
        primary = smart_data["primary_query"]
        must_include = smart_data["must_include"]
        must_exclude = smart_data["must_exclude"]
        intent = smart_data["intent_type"]

        def fetch_raw(target_query, fetch_limit=50):
            url = f"https://www.youtube.com/results?search_query={target_query.replace(' ', '+')}"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                r = requests.get(url, headers=headers, timeout=10)
                vids = re.findall(r'"videoId":"([^"]+)"', r.text)
                titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"', r.text)
                results = []
                seen = set()
                for vid_id, title in zip(vids, titles):
                    if vid_id in seen: continue
                    seen.add(vid_id)
                    try: name = title.encode('utf-8').decode('unicode-escape')
                    except Exception: name = title
                    results.append({
                        "name": name, "id": vid_id, "embed": f"https://www.youtube.com/embed/{vid_id}",
                        "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg", "type": "youtube"
                    })
                    if len(results) >= fetch_limit: break
                return results
            except: return []

        raw_results = fetch_raw(primary)
        
        # Fallback if primary is dry
        if len(raw_results) < 5:
            raw_results += fetch_raw(smart_data["backup_query"])

        # Pass 2: Re-rank
        scored_vids = self.rerank_titles(query, raw_results, intent)
        
        # Apply final scoring & filter
        final_list = []
        for v in scored_vids:
            score = self.compute_final_score(v, must_include, must_exclude)
            if score > 0:
                v["final_score"] = score
                final_list.append(v)
        
        final_list.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Requirement: At least 20 videos
        if len(final_list) < 20:
            print(f"[YouTube Pipeline] Warning: Only {len(final_list)} qualified videos found. Loosening filters.")
            # Add back lower-scoring videos if we are desperate for count
            unqualified = [v for v in scored_vids if v not in final_list]
            final_list += unqualified[:(20 - len(final_list))]
            
        return final_list[:30] # Return up to 30 for safe buffer

    def _build_tutorial_marker(self, local_tools, yt_videos):
        """
        Build the <!--TUTORIALS_START-->...<!--TUTORIALS_END--> marker
        with both local videos and dynamic YouTube results.
        """
        videos_data = []
        
        # 1. Add local videos first (if high priority)
        for tool in local_tools[:2]:
            videos_data.append({
                "name":     tool['name'],
                "category": tool.get('category', 'Local Tutorial'),
                "pricing":  tool.get('pricing', 'Free'),
                "path":     tool['video_tutorial'],
                "type":     "local"
            })
            
        # 2. Add dynamic YouTube results
        for vid in yt_videos:
            videos_data.append({
                "name":     vid['name'],
                "path":     vid['embed'],
                "thumbnail": vid['thumbnail'],
                "type":     "youtube",
                "category": "YouTube Tutorial",
                "pricing":  "Free"
            })

        if not videos_data:
            return ""

        marker = f"\n\n<!--TUTORIALS_START-->{json.dumps({'videos': videos_data})}<!--TUTORIALS_END-->"
        return marker

    def _append_random_tools_section(self, response_text: str, random_tools: list[dict]) -> str:
        """Append a simple 'Random tools' section at the end of the response."""
        if not random_tools:
            return response_text

        out = response_text.rstrip() + "\n\n---\n\n**Random tools (You may also like):**\n"
        for i, tool in enumerate(random_tools, 1):
            name = tool.get('name', 'Unknown')
            category = tool.get('category', 'AI Tools')
            pricing = tool.get('pricing', 'Free')
            out += f"{i}. **{name}** ({category}) - {pricing}"
            if tool.get('has_tutorial_video') and tool.get('video_tutorial'):
                out += " — Tutorial video available"
            out += "\n"
        return out

    def get_random_tools(self, exclude_tools: list[dict] | None = None, k: int = 5) -> list[dict]:
        """Return k random tools from the database, excluding any already-shown tools."""
        exclude_norm = set()
        if exclude_tools:
            for t in exclude_tools:
                exclude_norm.add(self._normalize_tool_name(t.get('name', '')))

        pool: list[dict] = []
        now = datetime.now()

        for category in self.tools_data.get('categories', []):
            for tool in category.get('tools', []):
                tool_name = tool.get('name', '')
                if self._normalize_tool_name(tool_name) in exclude_norm:
                    continue

                # Apply outdated filter to dynamic tools; keep fixed tools always eligible
                is_fixed = any(
                    self._normalize_tool_name(ft.get('name', '')) == self._normalize_tool_name(tool_name)
                    for ft in FIXED_TUTORIAL_TOOLS
                )

                if not is_fixed:
                    try:
                        last_verified = datetime.fromisoformat(tool.get('last_verified', '2024-01-01'))
                    except Exception:
                        last_verified = datetime.fromisoformat('2024-01-01')

                    if (now - last_verified).days >= 180:
                        continue

                pool.append({
                    **tool,
                    'category': category.get('name', tool.get('category', ''))
                })

        if not pool:
            return []

        if len(pool) <= k:
            # Sort by dynamic rank and return
            pool.sort(
                key=lambda x: self._dynamic_rank_score(
                    x,
                    any(
                        self._normalize_tool_name(ft.get('name', '')) == self._normalize_tool_name(x.get('name', ''))
                        for ft in FIXED_TUTORIAL_TOOLS
                    )
                ),
                reverse=True
            )
            return pool

        # Prefer tutorial-video tools slightly in random picks so users see videos more often.
        tutorial_pool = [t for t in pool if t.get('has_tutorial_video') and t.get('video_tutorial')]
        if len(tutorial_pool) >= k:
            return random.sample(tutorial_pool, k)

        picks = list(tutorial_pool)
        remaining = [t for t in pool if t not in tutorial_pool]
        if remaining:
            picks.extend(random.sample(remaining, min(k - len(picks), len(remaining))))
        return picks[:k]

    def format_response_with_tutorials(self, ai_response, local_tools, yt_videos):
        """Append the tutorial-video JSON marker to the AI response text."""
        return ai_response + self._build_tutorial_marker(local_tools, yt_videos)

    def add_tool(self, category_name, tool_data):
        """Add or update a tool in the database"""
        tool_data['last_verified'] = datetime.now().isoformat()

        for category in self.tools_data["categories"]:
            if category["name"].lower() == category_name.lower():
                for existing_tool in category["tools"]:
                    if existing_tool["name"].lower() == tool_data["name"].lower():
                        existing_tool.update(tool_data)
                        self.save_tools_data()
                        return True
                category["tools"].append(tool_data)
                self.save_tools_data()
                return True

        new_category = {
            "id": len(self.tools_data["categories"]) + 1,
            "name": category_name,
            "description": f"Tools for {category_name}",
            "tools": [tool_data]
        }
        self.tools_data["categories"].append(new_category)
        self.save_tools_data()
        return True

    def save_tools_data(self):
        """Persist tools data to JSON file"""
        self.tools_data['last_updated'] = datetime.now().isoformat()
        with open(os.path.join('Data', 'ai_tools_database.json'), 'w', encoding='utf-8') as f:
            json.dump(self.tools_data, f, indent=2)

    def get_tool_categories_overview(self):
        """Summary of all categories with tool counts"""
        overview = []
        for category in self.tools_data["categories"]:
            recent_tools = []
            for tool in category["tools"]:
                is_fixed = any(
                    self._normalize_tool_name(ft.get('name', '')) == self._normalize_tool_name(tool.get('name', ''))
                    for ft in FIXED_TUTORIAL_TOOLS
                )
                if is_fixed:
                    recent_tools.append(tool)
                else:
                    age = (datetime.now() - datetime.fromisoformat(
                        tool.get('last_verified', '2024-01-01'))).days
                    if age < 180:
                        recent_tools.append(tool)

            overview.append({
                "name":        category["name"],
                "description": category["description"],
                "tool_count":  len(recent_tools),
                "top_tool":    max(recent_tools, key=lambda x: x.get('ranking', 0))
                               if recent_tools else None
            })
        return overview