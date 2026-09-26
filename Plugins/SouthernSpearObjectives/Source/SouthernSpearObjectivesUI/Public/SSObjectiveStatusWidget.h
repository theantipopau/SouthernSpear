// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveStatusWidget.generated.h"

class UProgressBar;
class UTextBlock;

/**
 * Top-of-screen Objective Assault status: round and clock, active objective,
 * capture progress and captures. Builds its own widget tree in C++ so it needs
 * no asset; reads only replicated director/objective state through
 * FSSObjectiveHudModel. Display only: it changes nothing.
 */
UCLASS()
class SSOBJUI_API USSObjectiveStatusWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;

	void SetDirector(ASSObjectiveAssaultDirector* InDirector) { Director = InDirector; }

protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	TWeakObjectPtr<ASSObjectiveAssaultDirector> Director;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> HeaderText;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> ObjectiveText;

	UPROPERTY(Transient)
	TObjectPtr<UProgressBar> ProgressBar;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> ScoreText;
};
