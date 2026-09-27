// Copyright Southern Spear. All Rights Reserved.

#include "SSClassSelectWidget.h"

#include "Components/BackgroundBlur.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

namespace
{
	struct FRoleText
	{
		FText Name;
		FText Description;
		FText Standard; // kit on standard maps (matches Config/DefaultGame.ini Kits)
		FText Special;  // kit on Special Forces maps
	};

	const FRoleText& RoleText(int32 Index)
	{
		static const FRoleText Roles[] = {
			{ NSLOCTEXT("SSClass", "Rifleman", "RIFLEMAN"),
			  NSLOCTEXT("SSClass", "RiflemanDesc", "The backbone of the section. Take and hold the ground."),
			  NSLOCTEXT("SSClass", "RiflemanStd", "A88 · SPECTER OPTIC  +  A9"), NSLOCTEXT("SSClass", "RiflemanSF", "A416 · TA31  +  A9") },
			{ NSLOCTEXT("SSClass", "Medic", "MEDIC"),
			  NSLOCTEXT("SSClass", "MedicDesc", "Keeps the section in the fight. Healing is not in the game yet."),
			  NSLOCTEXT("SSClass", "MedicStd", "A88 · SPECTER OPTIC  +  A9"), NSLOCTEXT("SSClass", "MedicSF", "A4 · TA31  +  A9") },
			{ NSLOCTEXT("SSClass", "MachineGunner", "MACHINE GUNNER"),
			  NSLOCTEXT("SSClass", "MachineGunnerDesc", "Suppresses from the flank so the section can move."),
			  NSLOCTEXT("SSClass", "MachineGunnerStd", "A89 LIGHT SUPPORT WEAPON  +  A9"), NSLOCTEXT("SSClass", "MachineGunnerSF", "A89 LIGHT SUPPORT WEAPON  +  A9") },
			{ NSLOCTEXT("SSClass", "Sniper", "SNIPER"),
			  NSLOCTEXT("SSClass", "SniperDesc", "Long-range precision from overwatch."),
			  NSLOCTEXT("SSClass", "SniperStd", "A25 · TA648 OPTIC  +  A9"), NSLOCTEXT("SSClass", "SniperSF", "A25 · TA648 OPTIC  +  A9") },
			{ NSLOCTEXT("SSClass", "Grenadier", "GRENADIER"),
			  NSLOCTEXT("SSClass", "GrenadierDesc", "Indirect fire for cover. Launcher fire is not in the game yet."),
			  NSLOCTEXT("SSClass", "GrenadierStd", "A88G · UNDERBARREL LAUNCHER  +  A9"), NSLOCTEXT("SSClass", "GrenadierSF", "A4 · TA31  +  A9") },
		};
		return Roles[FMath::Clamp(Index, 0, 4)];
	}


}

bool USSClassSelectWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	UBackgroundBlur* Blur = T->ConstructWidget<UBackgroundBlur>();
	Blur->SetBlurStrength(6.f);
	Fill(Root, Blur);
	Fill(Root, Plate(T, SSPalette::Ink950(0.6f), FMargin(0.f)));

	UVerticalBox* Col = T->ConstructWidget<UVerticalBox>();
	Pin(Root, Col, FVector2D(0.5f, 0.5f), FVector2D(0.f, 0.f));
	Kicker = Text(T, 12, true, SSPalette::Brass300(), 300);
	AddV(Col, Kicker, 0.f, HAlign_Center);
	Heading = Text(T, 38, true, SSPalette::Sand100(), 120);
	AddV(Col, Heading, 2.f, HAlign_Center);
	AddV(Col, Rule(T, SSPalette::Brass500(), 2.f, 120.f), 10.f, HAlign_Center);

	const FName Handlers[] = {
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnRifleman),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnMedic),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnMachineGunner),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnSniper),
		GET_FUNCTION_NAME_CHECKED(USSClassSelectWidget, OnGrenadier),
	};
	UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
	AddV(Col, Row, 26.f, HAlign_Center);
	for (int32 Index = 0; Index < USSKitSelection::NumRoles; ++Index)
	{
		const FRoleText& Role = RoleText(Index);
		UButton* Card = MenuButton(T, FText::GetEmpty(), 0.f);
		Card->ClearChildren();
		UVerticalBox* Body = T->ConstructWidget<UVerticalBox>();
		USizeBox* Size = T->ConstructWidget<USizeBox>();
		Size->SetWidthOverride(212.f);
		Size->SetHeightOverride(210.f);
		Size->AddChild(Body);
		Card->AddChild(Size);

		UBorder* Edge = Plate(T, SSPalette::Brass500(), FMargin(0.f));
		USizeBox* EdgeSize = T->ConstructWidget<USizeBox>();
		EdgeSize->SetHeightOverride(3.f);
		EdgeSize->AddChild(Edge);
		AddV(Body, EdgeSize);
		CardEdges.Add(Edge);
		UTextBlock* Number = Text(T, 11, true, SSPalette::Brass300(), 260);
		Number->SetText(FText::FromString(FString::Printf(TEXT("0%d"), Index + 1)));
		AddV(Body, Number, 12.f);
		UTextBlock* Name = Text(T, 19, true, SSPalette::Sand100(), 100);
		Name->SetText(Role.Name);
		AddV(Body, Name, 2.f);
		UTextBlock* Desc = Text(T, 12, false, SSPalette::Sage200());
		Desc->SetText(Role.Description);
		Desc->SetAutoWrapText(true);
		AddV(Body, Desc, 8.f);
		AddV(Body, T->ConstructWidget<USpacer>(), 0.f)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		UTextBlock* Weapon = Text(T, 10, true, SSPalette::Brass300(), 160);
		Weapon->SetAutoWrapText(true);
		AddV(Body, Weapon, 8.f);
		WeaponTexts.Add(Weapon);

		FScriptDelegate Delegate;
		Delegate.BindUFunction(this, Handlers[Index]);
		Card->OnClicked.Add(Delegate);
		AddH(Row, Card)->SetPadding(FMargin(Index == 0 ? 0.f : 10.f, 0.f, 0.f, 0.f));
		Cards.Add(Card);
	}

	UTextBlock* Hint = Text(T, 11, true, SSPalette::Sage400(), 200);
	Hint->SetText(NSLOCTEXT("SSClass", "Hint", "CLICK A CLASS TO DEPLOY  ·  CHANGE LATER WITH  L"));
	AddV(Col, Hint, 22.f, HAlign_Center);
	return true;
}

void USSClassSelectWidget::Refresh()
{
	const USSKitSelection* Selection = GetWorld() ? GetWorld()->GetSubsystem<USSKitSelection>() : nullptr;
	const bool bSF = Selection && Selection->bSpecialForcesMap;
	for (int32 Index = 0; Index < WeaponTexts.Num(); ++Index)
	{
		WeaponTexts[Index]->SetText(bSF ? RoleText(Index).Special : RoleText(Index).Standard);
		CardEdges[Index]->SetBrushColor(bSF ? SSPalette::Sage200() : SSPalette::Brass500());
	}
	Kicker->SetText(bSF ? NSLOCTEXT("SSClass", "KickerSF", "SPECIAL FORCES  ·  CHOOSE YOUR ROLE")
		: NSLOCTEXT("SSClass", "KickerStd", "3 ACR  ·  CHOOSE YOUR ROLE"));
}

void USSClassSelectWidget::Open(bool bAfterDeath)
{
	Heading->SetText(bAfterDeath ? NSLOCTEXT("SSClass", "Redeploy", "REDEPLOY") : NSLOCTEXT("SSClass", "Deploy", "SELECT CLASS"));
	Refresh();
	Elapsed = 0.f;
	SetVisibility(ESlateVisibility::Visible);
	if (APlayerController* Player = GetOwningPlayer())
	{
		FInputModeGameAndUI Input;
		Input.SetWidgetToFocus(TakeWidget());
		Player->SetInputMode(Input);
		Player->SetShowMouseCursor(true);
	}
}

void USSClassSelectWidget::Close()
{
	SetVisibility(ESlateVisibility::Collapsed);
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->SetShowMouseCursor(false);
	}
}

void USSClassSelectWidget::Pick(ESSKitRole Role)
{
	if (USSKitSelection* Selection = GetWorld() ? GetWorld()->GetSubsystem<USSKitSelection>() : nullptr)
	{
		Selection->RequestKit(GetOwningPlayer(), Role);
	}
	Close();
}

void USSClassSelectWidget::OnRifleman()      { Pick(ESSKitRole::Rifleman); }
void USSClassSelectWidget::OnMedic()         { Pick(ESSKitRole::Medic); }
void USSClassSelectWidget::OnMachineGunner() { Pick(ESSKitRole::MachineGunner); }
void USSClassSelectWidget::OnSniper()        { Pick(ESSKitRole::Sniper); }
void USSClassSelectWidget::OnGrenadier()     { Pick(ESSKitRole::Grenadier); }

void USSClassSelectWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;
	for (int32 Index = 0; Index < Cards.Num(); ++Index)
	{
		Reveal(Cards[Index], Ease(Elapsed, 0.05f + 0.06f * Index, 0.35f), 20.f, /*bVertical=*/ true);
	}
}
