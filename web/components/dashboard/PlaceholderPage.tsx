import { Construction } from "lucide-react"

interface PlaceholderPageProps {
    title: string
    description?: string
}

export default function PlaceholderPage({ title, description }: PlaceholderPageProps) {
    return (
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] p-6 text-center">
            <div className="p-4 rounded-full bg-primary/10 mb-4">
                <Construction className="w-12 h-12 text-primary" />
            </div>
            <h1 className="text-2xl font-bold mb-2">{title}</h1>
            <p className="text-muted-foreground max-w-md">
                {description || "This page is currently under construction. Check back soon for updates!"}
            </p>
        </div>
    )
}
