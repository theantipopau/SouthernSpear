// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSObjectiveTypes.h"
#include "SSRoundBannerWidget.generated.h"

class ASSObjectiveAssaultDirector;
class UBorder;
class UTextBlock;
class UWidget;

/**
 * Centre-screen announcements for round events, derived from replicated round
 * state: round start (stand by), assault begins, objective secured (in the
 * capturing side's viewer-relative tone) and the round result. Eased in, held,
 * faded out. Built in C++.
 */
UCLASS()
class SSOBJUI_API USSRoundBannerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(ASSObjectiveAssaultDirector* InDirector);
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	void Show(const FText& Title, const FText& Subtitle, const FLinearColor& Tone);

	TWeakObjectPtr<ASSObjectiveAssaultDirector> Director;
	ESSRoundPhase LastPhase = ESSRoundPhase::WaitingToStart;
	int32 LastActive = INDEX_NONE;
	int32 LastRound = 0;
	float ShownFor = 100.f;

	UPROPERTY(Transient) TObjectPtr<UWidget> Banner;
	UPROPERTY(Transient) TObjectPtr<UBorder> ToneRule;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TitleText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubtitleText;
};
