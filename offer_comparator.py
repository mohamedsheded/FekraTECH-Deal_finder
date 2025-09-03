from typing import List, Dict, Any
import re
from models import ProductOffer, ComparisonResult

class OfferComparator:
    """Compares product offers to find the best deal"""

    def compare_offers(self, offers: List[ProductOffer]) -> ComparisonResult:
        """Compare multiple offers and return the best one with reasoning"""
        if not offers:
            raise ValueError("No offers to compare")

        if len(offers) == 1:
            return ComparisonResult(
                best_offer=offers[0],
                all_offers=offers,
                comparison_metrics={"single_offer": True},
                reasoning="Only one offer available"
            )

        # Score each offer
        scored_offers = []
        for offer in offers:
            score = self._calculate_offer_score(offer)
            scored_offers.append((offer, score))

        # Sort by score (higher is better)
        scored_offers.sort(key=lambda x: x[1], reverse=True)

        best_offer = scored_offers[0][0]
        best_score = scored_offers[0][1]

        # Generate comparison metrics
        metrics = self._generate_comparison_metrics(scored_offers)

        # Generate reasoning
        reasoning = self._generate_reasoning(scored_offers, best_offer, best_score)

        return ComparisonResult(
            best_offer=best_offer,
            all_offers=offers,
            comparison_metrics=metrics,
            reasoning=reasoning
        )

    def _calculate_offer_score(self, offer: ProductOffer) -> float:
        """Calculate a score for an offer based on multiple factors"""
        score = 0.0

        # Price scoring (lower price = higher score)
        if offer.price:
            price_score = self._extract_numeric_price(offer.price)
            if price_score > 0:
                # Normalize price score (lower price = higher score)
                # Assuming price range 0-1000 for normalization
                normalized_price = min(price_score / 1000, 1.0)
                score += (1.0 - normalized_price) * 40  # Price is 40% of total score

        # Source credibility scoring
        source_score = self._calculate_source_score(offer.source)
        score += source_score * 20  # Source is 20% of total score

        # Description quality scoring
        desc_score = self._calculate_description_score(offer.description)
        score += desc_score * 20  # Description is 20% of total score

        # Availability scoring
        if offer.availability:
            avail_score = self._calculate_availability_score(offer.availability)
            score += avail_score * 10  # Availability is 10% of total score

        # Rating scoring
        if offer.rating:
            rating_score = min(offer.rating / 5.0, 1.0)
            score += rating_score * 10  # Rating is 10% of total score

        return score

    def _extract_numeric_price(self, price_str: str) -> float:
        """Extract numeric price from price string"""
        try:
            # Remove currency symbols and extract numbers
            price_match = re.search(r'[\d,]+\.?\d*', price_str.replace(',', ''))
            if price_match:
                return float(price_match.group())
        except:
            pass
        return 0.0

    def _calculate_source_score(self, source: str) -> float:
        """Calculate credibility score for the source"""
        source_lower = source.lower()

        # Trusted sources get higher scores
        trusted_domains = ['amazon', 'bestbuy', 'walmart', 'target', 'newegg', 'bhphotovideo']
        for domain in trusted_domains:
            if domain in source_lower:
                return 1.0

        # Medium trust for known retailers
        medium_domains = ['ebay', 'etsy', 'shopify', 'woocommerce']
        for domain in medium_domains:
            if domain in source_lower:
                return 0.7

        # Default score for unknown sources
        return 0.5

    def _calculate_description_score(self, description: str) -> float:
        """Calculate quality score for description"""
        if not description:
            return 0.0

        score = 0.0

        # Length bonus
        if len(description) > 100:
            score += 0.3
        elif len(description) > 50:
            score += 0.2
        else:
            score += 0.1

        # Keyword bonus
        keywords = ['warranty', 'guarantee', 'free shipping', 'fast delivery', 'authentic', 'genuine']
        for keyword in keywords:
            if keyword.lower() in description.lower():
                score += 0.1

        return min(score, 1.0)

    def _calculate_availability_score(self, availability: str) -> float:
        """Calculate score based on availability"""
        avail_lower = availability.lower()

        if any(word in avail_lower for word in ['in stock', 'available', 'ready to ship']):
            return 1.0
        elif any(word in avail_lower for word in ['limited', 'few left']):
            return 0.7
        elif any(word in avail_lower for word in ['out of stock', 'unavailable']):
            return 0.0
        else:
            return 0.5

    def _generate_comparison_metrics(self, scored_offers: List[tuple]) -> Dict[str, Any]:
        """Generate comparison metrics for all offers"""
        metrics = {
            "total_offers": len(scored_offers),
            "price_range": {},
            "source_diversity": {},
            "score_distribution": {}
        }

        # Price range analysis
        prices = []
        for offer, _ in scored_offers:
            if offer.price:
                price_val = self._extract_numeric_price(offer.price)
                if price_val > 0:
                    prices.append(price_val)

        if prices:
            metrics["price_range"] = {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices)
            }

        # Source diversity
        sources = [offer.source for offer, _ in scored_offers]
        metrics["source_diversity"] = {
            "unique_sources": len(set(sources)),
            "sources": list(set(sources))
        }

        # Score distribution
        scores = [score for _, score in scored_offers]
        metrics["score_distribution"] = {
            "min_score": min(scores),
            "max_score": max(scores),
            "avg_score": sum(scores) / len(scores)
        }

        return metrics

    def _generate_reasoning(self, scored_offers: List[tuple], best_offer: ProductOffer, best_score: float) -> str:
        """Generate human-readable reasoning for the best offer selection"""
        reasoning_parts = []

        # Main reason
        if best_score > 80:
            reasoning_parts.append("This offer received an excellent overall score")
        elif best_score > 60:
            reasoning_parts.append("This offer received a good overall score")
        else:
            reasoning_parts.append("This offer was selected as the best available option")

        # Price reasoning
        if best_offer.price:
            price_val = self._extract_numeric_price(best_offer.price)
            if price_val > 0:
                # Compare with other offers
                other_prices = []
                for offer, _ in scored_offers:
                    if offer != best_offer and offer.price:
                        other_price = self._extract_numeric_price(offer.price)
                        if other_price > 0:
                            other_prices.append(other_price)

                if other_prices:
                    if price_val < min(other_prices):
                        reasoning_parts.append("it offers the lowest price among all options")
                    elif price_val < sum(other_prices) / len(other_prices):
                        reasoning_parts.append("it offers a competitive price below the average")

        # Source reasoning
        source_score = self._calculate_source_score(best_offer.source)
        if source_score > 0.8:
            reasoning_parts.append("it comes from a highly trusted retailer")
        elif source_score > 0.6:
            reasoning_parts.append("it comes from a reputable retailer")

        # Description reasoning
        if best_offer.description and len(best_offer.description) > 100:
            reasoning_parts.append("it provides detailed product information")

        # Rating reasoning
        if best_offer.rating and best_offer.rating > 4.0:
            reasoning_parts.append("it has excellent customer ratings")
        elif best_offer.rating and best_offer.rating > 3.5:
            reasoning_parts.append("it has good customer ratings")

        if not reasoning_parts:
            reasoning_parts.append("it was selected based on overall offer quality")

        return ". ".join(reasoning_parts) + "."
