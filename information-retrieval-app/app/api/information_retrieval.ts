"use server";
const baseUrl = process.env.IR_API_URL;

export async function getVectorSpaceArticles(url: string): Promise<ArticleResult[]> {  
    try {
        const response = await fetch(`${baseUrl}${url}`);

        if (!response.ok) {
            throw new Error(`Vector space request failed with status ${response.status}`);
        }

        const data = await response.json();
        const articles: ArticleResult[] = data as ArticleResult[];

        return articles;
    } catch (error) {
        console.error(`Error fetching vector space articles: ${error}`);
        return [];
    }
}

export async function getBooleanArticles(url: string, filters: Filter[]): Promise<ArticleResult[]>{
    try {
        const response = await fetch(`${baseUrl}${url}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filters)
        });

        if (!response.ok) {
            throw new Error(`Boolean request failed with status ${response.status}`);
        }

        const data = await response.json();
        const articles: ArticleResult[] = data as ArticleResult[];

        return articles;
    } catch (error) {
        console.error(`Error fetching boolean articles: ${error}`);
        return [];
    }
}